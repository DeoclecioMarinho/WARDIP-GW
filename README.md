# WARDIP-GW — Dashboard de centros de formação
1. Importe o XLSForm no KoboToolbox, teste no Enketo/KoboCollect e implemente o projeto.
2. Coloque app.py e requirements.txt no repositório privado GitHub. Não publique credenciais nem exportações.
3. Execute localmente: `pip install -r requirements.txt` e `streamlit run app.py`.
4. Copie .streamlit/secrets.example.toml para .streamlit/secrets.toml e configure o servidor, UID e token Kobo. No Streamlit Community Cloud configure os mesmos valores em Secrets, sem enviar o ficheiro para GitHub.
5. Use um token com permissões mínimas de leitura. Restrinja o acesso ao dashboard a utilizadores autorizados; não disponibilize publicamente dados de localização e identificação. A aplicação não inclui autenticação própria.
6. Alternativamente carregue uma exportação CSV/XLSX com nomes XML. O painel exclui as fichas não autorizadas. Não elimina duplicados automaticamente. Os totais contabilizam fichas, não centros únicos confirmados.
7. Sem universo de referência, não existe taxa de cobertura. O painel mostra apenas cobertura observada. Teste submissões autorizadas, recusadas, GPS e duplicados antes de produção.

## Versão 2 — formulário v3
Inclui modo Demonstração com seis centros inteiramente fictícios. A lista de regiões e sectores é extraída do XLSForm v3. O número da ficha é apenas uma referência visual, não uma chave única: usar id_registo. A consulta individual contém contactos; publicar apenas com acesso restrito. Os alertas não eliminam registos. Sem universo de referência, não existe taxa de cobertura real.

Publicação: criar repositório privado GitHub, carregar todos os ficheiros (incluindo .streamlit/config.toml), selecionar app.py no Streamlit Community Cloud e inserir KOBO_URL, KOBO_ASSET_UID e KOBO_TOKEN nos Secrets. Não carregar secrets.toml no GitHub. Configurar acesso privado antes de usar dados reais.
