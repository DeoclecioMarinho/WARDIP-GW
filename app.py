import os
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from urllib.parse import urlparse
st.set_page_config(page_title='WARDIP-GW | Centros de informática',page_icon='🖥️',layout='wide')
REG=dict(zip('bafata biombo bolama cacheu gabu oio quinara tombali sab'.split(),['Bafatá','Biombo','Bolama/Bijagós','Cacheu','Gabú','Oio','Quinara','Tombali','Sector Autónomo de Bissau']))
TIP=dict(zip('publico privado ong comunitario religioso outro'.split(),['Público','Privado','ONG / associação','Comunitário','Religioso','Outro']))
NEC=dict(zip('equipamentos internet energia formadores material outra'.split(),['Equipamentos','Internet','Energia','Formação de formadores','Material didático','Outra']))
RES=dict(zip('armazenados reutilizados recicladores lixo queimados outro'.split(),['Armazenados','Reutilizados','Recicladores','Deitados fora','Queimados','Outro']))
NUM=['formandos_h','formandos_m','jovens_h','jovens_m','pcd_h','pcd_m','formadores_h','formadores_m','computadores_ok','computadores_avariados','salas','capacidade','turnos','horas_energia','acumulados']
def setting(k,default=''):
    try: return st.secrets.get(k,os.getenv(k,default))
    except Exception: return os.getenv(k,default)
@st.cache_data(ttl=300,show_spinner=False)
def fetch(base,uid,token):
    url=f'{base.rstrip("/")}/api/v2/assets/{uid}/data/?limit=1000'; rows=[]; seen=set()
    while url:
        if url in seen or urlparse(url).netloc!=urlparse(base).netloc or urlparse(url).scheme!='https': raise ValueError('Paginação inválida')
        seen.add(url); r=requests.get(url,headers={'Authorization':f'Token {token}'},timeout=40);r.raise_for_status(); page=r.json();rows.extend(page['results']);url=page.get('next')
    return pd.DataFrame(rows)
def normalize(df):
    df=df.copy(); df.columns=[str(c).split('/')[-1] for c in df.columns]
    if df.columns.duplicated().any(): raise ValueError('Colunas duplicadas após normalização.')
    for c in NUM: df[c]=pd.to_numeric(df[c],errors='coerce') if c in df else float('nan')
    for c in ['regiao','sector','localidade','centro','tipo','autorizacao','internet','licenca','interesse','acessibilidade','estado','mgr','queixas','conduta','seguranca','agua','armazenamento','necessidades','residuos','energia','gps','tecnico','data_levantamento','ficha']:
        if c not in df: df[c]=pd.NA
    df['Região']=df.regiao.map(REG).fillna(df.regiao);df['Tipo']=df.tipo.map(TIP).fillna(df.tipo)
    for k in ['formandos','jovens','pcd','formadores']: df[k+'_total']=df[[k+'_h',k+'_m']].sum(axis=1,min_count=2)
    return df
st.title('WARDIP-GW | Centros de formação em informática')
st.caption('Mapeamento nacional · Seguimento da recolha · Diagnóstico de capacidades')
with st.sidebar:
    st.header('Fonte de dados'); mode=st.radio('Modo',['Kobo API','Ficheiro CSV/XLSX'])
    if mode=='Kobo API':
        base=setting('KOBO_URL','https://kf.kobotoolbox.org');uid=setting('KOBO_ASSET_UID');token=setting('KOBO_TOKEN')
        st.caption('Configure as credenciais no servidor (Secrets). Não as publique no GitHub.')
        if st.button('Atualizar dados'): fetch.clear()
        if not uid or not token: st.info('Configure KOBO_ASSET_UID e KOBO_TOKEN.');st.stop()
        try: raw=fetch(base,uid,token)
        except Exception as e: st.error(f'Falha na ligação ao Kobo ({type(e).__name__}). Verifique a configuração.');st.stop()
    else:
        f=st.file_uploader('Exportação Kobo com nomes XML (não rótulos)',type=['csv','xlsx'])
        if f is None: st.stop()
        try: raw=pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
        except Exception: st.error('Não foi possível ler o ficheiro.');st.stop()
if raw.empty: st.info('Ainda não existem submissões.');st.stop()
try: df=normalize(raw)
except ValueError as e: st.error(str(e));st.stop()
if 'autorizacao' not in [str(c).split('/')[-1] for c in raw.columns]: st.error('A coluna de autorização não existe. Use a exportação com nomes XML.');st.stop()
refusals=int((df.autorizacao=='nao').sum());df=df[df.autorizacao=='sim'].copy()
st.caption(f'Submissões recebidas: {len(raw)} | Sem autorização: {refusals} | Autorizadas: {len(df)}')
with st.sidebar:
    for col,label in [('Região','Região'),('sector','Sector'),('Tipo','Tipo de centro'),('tecnico','Técnico')]:
        opts=sorted(df[col].dropna().astype(str).unique());sel=st.multiselect(label,opts)
        if sel: df=df[df[col].astype(str).isin(sel)]
    search=st.text_input('Pesquisar centro')
    if search: df=df[df.centro.fillna('').astype(str).str.contains(search,case=False,regex=False)]
if df.empty: st.info('Sem registos autorizados para os filtros selecionados.');st.stop()
# Potential duplicates remain visible, no automatic merging.
key=df[['regiao','sector','centro']].fillna('').astype(str).apply(lambda s:s.str.strip().str.casefold());df['possivel_duplicado']=key.duplicated(keep=False) & key.ne('').all(axis=1)
if df.possivel_duplicado.any(): st.warning('Existem possíveis duplicados. Os totais são provisórios até à validação.')
def total(c):
    v=df[c].sum(min_count=1);return '—' if pd.isna(v) else f'{v:,.0f}'.replace(',',' ')
def pct(c,value='sim'):
    s=df[c].dropna();return '—' if s.empty else f'{100*s.eq(value).mean():.1f}%'
for col,(label,value) in zip(st.columns(5),[('Fichas autorizadas',len(df)),('Formandos',total('formandos_total')),('Formadores',total('formadores_total')),('Computadores operacionais',total('computadores_ok')),('Centros com internet',pct('internet'))]): col.metric(label,value)
tabs=st.tabs(['Visão geral','Formação e inclusão','Infraestruturas','Parcerias e necessidades','Salvaguardas e resíduos','Mapa','Qualidade e seguimento'])
def bar(col,title):
    s=df[col].dropna().value_counts().rename_axis('Categoria').reset_index(name='Fichas');st.plotly_chart(px.bar(s,x='Categoria',y='Fichas',title=title),use_container_width=True)
def multi(col,labels,title):
    s=df[col].dropna().astype(str).str.split().explode().value_counts().rename_axis('Categoria').reset_index(name='Fichas');s['Categoria']=s.Categoria.map(labels).fillna(s.Categoria);st.plotly_chart(px.bar(s,x='Fichas',y='Categoria',orientation='h',title=title),use_container_width=True)
with tabs[0]:
    a,b=st.columns(2)
    with a:bar('Região','Fichas por região')
    with b:bar('Tipo','Tipologia dos centros')
    st.caption('Cobertura territorial observada; sem lista de centros previstos não é possível calcular a taxa de cobertura.')
    st.dataframe(df.groupby('Região',dropna=False).agg(Fichas=('centro','size'),Formandos=('formandos_total',lambda x:x.sum(min_count=1)),Computadores=('computadores_ok',lambda x:x.sum(min_count=1))),use_container_width=True)
with tabs[1]:
    rows=[]
    for k,label in [('formandos','Formandos'),('jovens','Jovens até 35 anos'),('pcd','Pessoas com deficiência'),('formadores','Formadores')]:
        for g,lab in [('h','Homens'),('m','Mulheres')]:rows.append({'Grupo':label,'Sexo':lab,'Total':df[k+'_'+g].sum(min_count=1)})
    st.plotly_chart(px.bar(pd.DataFrame(rows),x='Grupo',y='Total',color='Sexo',barmode='group'),use_container_width=True);st.caption('Jovens e pessoas com deficiência são subconjuntos dos formandos e podem sobrepor-se.')
with tabs[2]:
    a,b,c=st.columns(3);a.metric('Salas',total('salas'));b.metric('Computadores avariados',total('computadores_avariados'));c.metric('Acessibilidade plena',pct('acessibilidade'))
    for field,title in [('internet','Internet'),('estado','Estado das instalações'),('acessibilidade','Acessibilidade'),('agua','Água e saneamento'),('seguranca','Segurança')]:bar(field,title)
    multi('energia',{'rede':'Rede pública','gerador':'Gerador','solar':'Solar','nenhuma':'Nenhuma'},'Fontes de energia')
with tabs[3]:
    st.metric('Interesse em colaborar',pct('interesse'));multi('necessidades',NEC,'Principais necessidades');bar('licenca','Registo oficial');st.dataframe(df[['centro','Região','sector','interesse','necessidades']],hide_index=True,use_container_width=True)
with tabs[4]:
    for c,title in [('mgr','Conhecimento do MGR'),('queixas','Mecanismo de queixas'),('conduta','Regras de conduta e proteção'),('armazenamento','Armazenamento seguro')]:bar(c,title)
    multi('residuos',RES,'Destino dos equipamentos');st.metric('Equipamentos acumulados',total('acumulados'))
with tabs[5]:
    xy=df.gps.fillna('').astype(str).str.split(expand=True)
    if xy.shape[1]>=2:
        geo=pd.DataFrame({'lat':pd.to_numeric(xy[0],errors='coerce'),'lon':pd.to_numeric(xy[1],errors='coerce'),'Centro':df.centro}).dropna(subset=['lat','lon']);geo=geo[geo.lat.between(-90,90)&geo.lon.between(-180,180)&~((geo.lat==0)&(geo.lon==0))]
        if not geo.empty: st.map(geo[['lat','lon']]);st.caption(f'{len(geo)} fichas com GPS válido de {len(df)}.')
        else: st.info('Sem GPS válido.')
    else: st.info('Sem coordenadas GPS.')
with tabs[6]:
    st.subheader('Seguimento por técnico');st.dataframe(df.groupby('tecnico',dropna=False).size().rename('Fichas'),use_container_width=True)
    dates=pd.to_datetime(df.data_levantamento,errors='coerce').dt.date.value_counts().sort_index();st.line_chart(dates)
    st.subheader('Verificações');st.write('Possíveis duplicados:',int(df.possivel_duplicado.sum()));st.write('Sem GPS:',int(df.gps.fillna('').eq('').sum()));st.write('Sem nome do centro:',int(df.centro.fillna('').eq('').sum()));st.write('Inconsistências nos subconjuntos de formandos:',int(((df.jovens_h>df.formandos_h)|(df.jovens_m>df.formandos_m)|(df.pcd_h>df.formandos_h)|(df.pcd_m>df.formandos_m)).sum()))
    cols=['ficha','centro','Região','sector','localidade','Tipo','tecnico','data_levantamento','formandos_total','formadores_total','computadores_ok','internet','interesse','possivel_duplicado'];out=df[cols];st.dataframe(out,hide_index=True,use_container_width=True);st.download_button('Exportar lista filtrada (CSV)',out.to_csv(index=False).encode('utf-8-sig'),'centros_wardip.csv','text/csv')
