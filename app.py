import os
import json
from pathlib import Path
from quality import audit
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from urllib.parse import urlparse
st.set_page_config(page_title='WARDIP-GW | Centros de informática',page_icon='🖥️',layout='wide')
SCHEMA=json.loads(Path(__file__).with_name('schema.json').read_text())
CHOICES=SCHEMA['choices']; REG=CHOICES['regiao']; TIP=CHOICES['tipo']; NEC=CHOICES['necessidades']; RES=CHOICES['residuos']; SEC=CHOICES['sector']
NUM=['formandos_h','formandos_m','jovens_h','jovens_m','pcd_h','pcd_m','formadores_h','formadores_m','computadores_ok','computadores_avariados','salas','capacidade','turnos','horas_energia','acumulados','ano']
def setting(k,default=''):
    try: return st.secrets.get(k,os.getenv(k,default))
    except Exception: return os.getenv(k,default)
@st.cache_data(ttl=300,show_spinner=False)
def fetch(base,uid,token):
    if urlparse(base).scheme != 'https' or not urlparse(base).netloc: raise ValueError('Servidor HTTPS obrigatório')
    url=f'{base.rstrip("/")}/api/v2/assets/{uid}/data/?limit=1000'; rows=[]; seen=set()
    while url:
        if url in seen or urlparse(url).netloc!=urlparse(base).netloc or urlparse(url).scheme!='https': raise ValueError('Paginação inválida')
        seen.add(url); r=requests.get(url,headers={'Authorization':f'Token {token}'},timeout=40);r.raise_for_status(); page=r.json();rows.extend(page['results']);url=page.get('next')
    return pd.DataFrame(rows)
def normalize(df):
    df=df.copy(); df.columns=[str(c).split('/')[-1] for c in df.columns]
    if df.columns.duplicated().any(): raise ValueError('Colunas duplicadas após normalização.')
    for c in NUM: df[c]=pd.to_numeric(df[c],errors='coerce') if c in df else float('nan')
    for c in ['regiao','sector','localidade','centro','tipo','autorizacao','internet','licenca','interesse','acessibilidade','estado','mgr','queixas','conduta','seguranca','agua','armazenamento','necessidades','residuos','energia','gps','tecnico','data_levantamento','ficha','id_registo','morada','responsavel','telefone','contacto_digital','qualificacao','linguas','parceiros','areas','colaborou','projetos','internet_tipo','internet_velocidade','assinatura_tecnico','assinatura_responsavel']:
        if c not in df: df[c]=pd.NA
    df['Sector']=df.sector.map(SEC).fillna(df.sector);df['Região']=df.regiao.map(REG).fillna(df.regiao);df['Tipo']=df.tipo.map(TIP).fillna(df.tipo)
    for k in ['formandos','jovens','pcd','formadores']: df[k+'_total']=df[[k+'_h',k+'_m']].sum(axis=1,min_count=2)
    return df
st.markdown("""<style>
[data-testid="stSidebar"] {background:#102e3b;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#dcebee;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:5px;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:9px 10px;border-radius:8px;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#22626a;}
[data-testid="stSidebar"] button {border:1px solid #64838c;}
[data-testid="stMetric"] {border:1px solid #dce7e9;border-radius:12px;padding:15px;background:#fff;}
[data-testid="stMetricLabel"] {white-space:normal;}
.block-container {padding-top:2.5rem;}
.wardip-brand {color:#fff;font-size:25px;font-weight:800;letter-spacing:1px;}
.wardip-sub {color:#a8cbd0;font-size:12px;margin:4px 0 20px;}
.wardip-kicker {color:#126b70;font-size:12px;font-weight:700;letter-spacing:2px;}
</style>""",unsafe_allow_html=True)
PAGES=['Visão geral','Formação e inclusão','Infraestruturas','Parcerias e necessidades','Salvaguardas e resíduos','Mapa','Qualidade e seguimento','Ficha do centro']
ICONS=['▦','◉','▤','◇','♻','⌖','✓','▣']
with st.sidebar:
    st.markdown('<div class="wardip-brand">WARDIP-GW</div><div class="wardip-sub">OBSERVATÓRIO DE FORMAÇÃO DIGITAL<br>Guiné-Bissau</div>',unsafe_allow_html=True)
    st.caption('NAVEGAÇÃO')
    page=st.radio('Navegação',PAGES,format_func=lambda x: f'{ICONS[PAGES.index(x)]}  {x}',label_visibility='collapsed')
    st.divider()
    st.caption('SINCRONIZAÇÃO')
    refresh=st.button('↻ Atualizar dados',use_container_width=True)
    if refresh: fetch.clear()
base=setting('KOBO_URL','https://kf.kobotoolbox.org');uid=setting('KOBO_ASSET_UID');token=setting('KOBO_TOKEN')
st.markdown('<div class="wardip-kicker">WARDIP-GW / MAPEAMENTO NACIONAL</div>',unsafe_allow_html=True)
st.title(page)
st.caption('Centros de formação em informática · Guiné-Bissau')
if not uid or not token:
    st.sidebar.error('Ligação não configurada');st.error('Configuração Kobo em falta. Contacte o administrador.');st.stop()
try:
    with st.spinner('A sincronizar com o KoboToolbox…'): raw=fetch(base,uid,token)
except Exception as e:
    st.sidebar.error('Ligação indisponível');st.error(f'Falha na ligação ao Kobo ({type(e).__name__}). Verifique a configuração.');st.stop()
st.sidebar.success('Kobo API · Ligação ativa')
st.sidebar.caption(f'{len(raw)} submissões recebidas · Atualização automática ao consultar após 5 min')
if raw.empty:
    for col,label in zip(st.columns(3),['Fichas recebidas','Fichas autorizadas','Fichas por validar']): col.metric(label,0)
    st.info('Ainda não existem submissões. Esta área será preenchida assim que os primeiros registos chegarem do Kobo.')
    st.markdown('#### Aguardando o início da recolha')
    st.caption('A ligação ao servidor foi estabelecida. Não são apresentados dados fictícios nem indicadores sem informação.')
    st.stop()
try: df=normalize(raw)
except ValueError as e: st.error(str(e));st.stop()
if 'autorizacao' not in [str(c).split('/')[-1] for c in raw.columns]: st.error('A coluna de autorização não existe. Use a exportação com nomes XML.');st.stop()
refusals=int((df.autorizacao=='nao').sum());df=df[df.autorizacao=='sim'].copy()
st.caption(f'Submissões recebidas: {len(raw)} | Sem autorização: {refusals} | Autorizadas: {len(df)}')
with st.sidebar:
    st.divider()
    st.caption('FILTROS DE ANÁLISE')
    for col,label in [('Região','Região'),('Sector','Sector'),('Tipo','Tipo de centro'),('tecnico','Técnico')]:
        opts=sorted(df[col].dropna().astype(str).unique());sel=st.multiselect(label,opts)
        if sel: df=df[df[col].astype(str).isin(sel)]
    datas=pd.to_datetime(df.data_levantamento,errors='coerce').dropna()
    if not datas.empty:
        periodo=st.date_input('Período do levantamento',(datas.min().date(),datas.max().date()))
        if len(periodo)==2:
            df=df[pd.to_datetime(df.data_levantamento,errors='coerce').dt.date.between(*periodo)]
    search=st.text_input('Pesquisar centro')
    if search: df=df[df.centro.fillna('').astype(str).str.contains(search,case=False,regex=False)]
if df.empty: st.info('Sem registos autorizados para os filtros selecionados.');st.stop()
# Potential duplicates remain visible, no automatic merging.
key=df[['regiao','sector','centro']].fillna('').astype(str).apply(lambda s:s.str.strip().str.casefold());df['possivel_duplicado']=key.duplicated(keep=False) & key.ne('').all(axis=1)
df['alertas']=audit(df,SCHEMA['sector_region'])
if df.possivel_duplicado.any(): st.warning('Existem possíveis duplicados. Os totais são provisórios até à validação.')
def total(c):
    v=df[c].sum(min_count=1);return '—' if pd.isna(v) else f'{v:,.0f}'.replace(',',' ')
def pct(c,value='sim'):
    s=df[c].dropna();return '—' if s.empty else f'{100*s.eq(value).mean():.1f}%'
for col,(label,value) in zip(st.columns(5),[('Fichas autorizadas',len(df)),('Formandos',total('formandos_total')),('Formadores',total('formadores_total')),('Computadores operacionais',total('computadores_ok')),('Centros com internet',pct('internet'))]): col.metric(label,value)

def bar(col,title):
    s=df[col].dropna().replace({'sim':'Sim','nao':'Não','parcial':'Parcial','bom':'Bom','razoavel':'Razoável','mau':'Mau'}).value_counts().rename_axis('Categoria').reset_index(name='Fichas');st.plotly_chart(px.bar(s,x='Categoria',y='Fichas',title=title),use_container_width=True)
def multi(col,labels,title):
    s=df[col].dropna().astype(str).str.split().explode().value_counts().rename_axis('Categoria').reset_index(name='Fichas');s['Categoria']=s.Categoria.map(labels).fillna(s.Categoria);st.plotly_chart(px.bar(s,x='Fichas',y='Categoria',orientation='h',title=title),use_container_width=True)
if page == PAGES[0]:
    a,b=st.columns(2)
    with a:bar('Região','Fichas por região')
    with b:bar('Tipo','Tipologia dos centros')
    st.caption('Cobertura territorial observada; sem lista de centros previstos não é possível calcular a taxa de cobertura.')
    st.dataframe(df.groupby('Região',dropna=False).agg(Fichas=('centro','size'),Formandos=('formandos_total',lambda x:x.sum(min_count=1)),Computadores=('computadores_ok',lambda x:x.sum(min_count=1))),use_container_width=True)
if page == PAGES[1]:
    rows=[]
    for k,label in [('formandos','Formandos'),('jovens','Jovens até 35 anos'),('pcd','Pessoas com deficiência'),('formadores','Formadores')]:
        for g,lab in [('h','Homens'),('m','Mulheres')]:rows.append({'Grupo':label,'Sexo':lab,'Total':df[k+'_'+g].sum(min_count=1)})
    st.plotly_chart(px.bar(pd.DataFrame(rows),x='Grupo',y='Total',color='Sexo',barmode='group'),use_container_width=True);st.caption('Jovens e pessoas com deficiência são subconjuntos dos formandos e podem sobrepor-se.')
if page == PAGES[2]:
    a,b,c=st.columns(3);a.metric('Salas',total('salas'));b.metric('Computadores avariados',total('computadores_avariados'));c.metric('Acessibilidade plena',pct('acessibilidade'))
    for field,title in [('internet','Internet'),('estado','Estado das instalações'),('acessibilidade','Acessibilidade'),('agua','Água e saneamento'),('seguranca','Segurança')]:bar(field,title)
    multi('energia',{'rede':'Rede pública','gerador':'Gerador','solar':'Solar','nenhuma':'Nenhuma'},'Fontes de energia')
if page == PAGES[3]:
    st.metric('Interesse em colaborar',pct('interesse'));multi('necessidades',NEC,'Principais necessidades');bar('licenca','Registo oficial');st.dataframe(df[['centro','Região','Sector','interesse','necessidades']],hide_index=True,use_container_width=True)
if page == PAGES[4]:
    for c,title in [('mgr','Conhecimento do MGR'),('queixas','Mecanismo de queixas'),('conduta','Regras de conduta e proteção'),('armazenamento','Armazenamento seguro')]:bar(c,title)
    multi('residuos',RES,'Destino dos equipamentos');st.metric('Equipamentos acumulados',total('acumulados'))
if page == PAGES[5]:
    xy=df.gps.fillna('').astype(str).str.split(expand=True)
    if xy.shape[1]>=2:
        geo=pd.DataFrame({'lat':pd.to_numeric(xy[0],errors='coerce'),'lon':pd.to_numeric(xy[1],errors='coerce'),'Centro':df.centro}).dropna(subset=['lat','lon']);geo=geo[geo.lat.between(-90,90)&geo.lon.between(-180,180)&~((geo.lat==0)&(geo.lon==0))]
        if not geo.empty: st.map(geo[['lat','lon']]);st.caption(f'{len(geo)} fichas com GPS válido de {len(df)}.')
        else: st.info('Sem GPS válido.')
    else: st.info('Sem coordenadas GPS.')
if page == PAGES[6]:
    st.subheader('Seguimento por técnico');st.dataframe(df.groupby('tecnico',dropna=False).size().rename('Fichas'),use_container_width=True)
    dates=pd.to_datetime(df.data_levantamento,errors='coerce').dt.date.value_counts().sort_index();st.line_chart(dates)
    st.subheader('Verificações');st.write('Possíveis duplicados:',int(df.possivel_duplicado.sum()));st.write('Sem GPS:',int(df.gps.fillna('').eq('').sum()));st.write('Sem nome do centro:',int(df.centro.fillna('').eq('').sum()));st.write('Inconsistências nos subconjuntos de formandos:',int(((df.jovens_h>df.formandos_h)|(df.jovens_m>df.formandos_m)|(df.pcd_h>df.formandos_h)|(df.pcd_m>df.formandos_m)).sum()))
    st.dataframe(df.loc[df.alertas.ne(''),['ficha','centro','Região','Sector','alertas']],hide_index=True,use_container_width=True)
    cols=['id_registo','ficha','centro','Região','Sector','localidade','Tipo','tecnico','data_levantamento','formandos_total','formadores_total','computadores_ok','internet','interesse','possivel_duplicado','alertas'];out=df[cols];st.dataframe(out,hide_index=True,use_container_width=True);st.download_button('Exportar lista filtrada (CSV)',out.to_csv(index=False).encode('utf-8-sig'),'centros_wardip.csv','text/csv')

if page == PAGES[7]:
    st.subheader('Consulta individual')
    options=list(range(len(df)))
    i=st.selectbox('Centro',options,format_func=lambda i:f"{df.iloc[i].ficha} — {df.iloc[i].centro} ({df.iloc[i]['Região']})")
    r=df.iloc[i]
    st.markdown(f"### {r.centro}")
    for label,fields in [('Identificação',['id_registo','ficha','Região','Sector','localidade','Tipo','morada','responsavel','telefone','contacto_digital']),('Formação',['formandos_total','jovens_total','pcd_total','formadores_total','capacidade','turnos','qualificacao','linguas']),('Infraestruturas',['salas','computadores_ok','computadores_avariados','internet','internet_tipo','internet_velocidade','energia','horas_energia','acessibilidade','estado']),('Parcerias e salvaguardas',['licenca','parceiros','interesse','areas','necessidades','mgr','queixas','conduta','residuos','armazenamento','alertas'])]:
        with st.expander(label,expanded=True):
            st.dataframe(pd.DataFrame({'Campo':fields,'Resposta':[str(r.get(f,'')) if pd.notna(r.get(f)) else '—' for f in fields]}),hide_index=True,use_container_width=True)
    st.download_button('Exportar ficha (CSV)',df.iloc[[i]].drop(columns=['assinatura_tecnico','assinatura_responsavel'],errors='ignore').to_csv(index=False).encode('utf-8-sig'),'ficha_centro.csv','text/csv')
