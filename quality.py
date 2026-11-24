import pandas as pd

def audit(df, sector_region):
    def check(r):
        issues=[]
        if not str(r.get('id_registo','')).strip() or pd.isna(r.get('id_registo')): issues.append('Sem UUID')
        if sector_region.get(r.sector)!=r.regiao: issues.append('Região/sector incompatíveis')
        if pd.isna(r.centro) or not str(r.centro).strip(): issues.append('Sem nome')
        for c in ['formandos_h','formandos_m','jovens_h','jovens_m','pcd_h','pcd_m','formadores_h','formadores_m','salas','computadores_ok','computadores_avariados','capacidade','turnos']:
            v=r[c]
            if pd.isna(v) or v<0 or v%1: issues.append('Quantidade inválida: '+c)
        for sex in ['h','m']:
            for group in ['jovens','pcd']:
                if r[group+'_'+sex]>r['formandos_'+sex]: issues.append(group+' excede formandos ('+sex+')')
        if pd.notna(r.horas_energia) and not 0<=r.horas_energia<=24: issues.append('Horas de energia inválidas')
        for c in ['energia','necessidades']:
            tokens=str(r[c]).split()
            if 'nenhuma' in tokens and len(tokens)>1: issues.append('Nenhuma combinada: '+c)
        date=pd.to_datetime(r.data_levantamento,errors='coerce')
        if pd.isna(date) or date.date()>pd.Timestamp.today().date(): issues.append('Data inválida')
        if r.possivel_duplicado: issues.append('Possível centro duplicado')
        return '; '.join(issues)
    return df.apply(check,axis=1)
