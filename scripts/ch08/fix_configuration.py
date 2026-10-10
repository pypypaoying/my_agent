import os
from dotenv import dotenv_values
from my_agent.config import load_project_env
from neo4j import GraphDatabase

env_path = load_project_env()
with GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USERNAME'],os.environ['NEO4J_PASSWORD'])) as driver:
    with driver.session() as session:
        info=session.run('CALL db.info()').single().data()
        database_name=info['name']
        assert session.run('RETURN 1 AS ok').single()['ok']==1
print('Neo4j 实际默认数据库: '+database_name+'，查询通过',flush=True)
with env_path.open('r',encoding='utf-8',newline='') as handle:
    source=handle.read()
lines=source.splitlines(keepends=True)
values=dotenv_values(env_path)
updates={}
if values.get('NEO4J_DATABASE') != database_name:
    updates['NEO4J_DATABASE']=database_name
if values.get('QDRANT_VECTOR_SIZE') != '1024':
    updates['QDRANT_VECTOR_SIZE']='1024'
for i,line in enumerate(lines):
    key=line.split('=',1)[0].strip()
    if key in updates:
        ending='\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
        lines[i]=key+'='+updates[key]+ending
if updates:
    with env_path.open('w',encoding='utf-8',newline='') as handle:
        handle.write(''.join(lines))
    print('已修正配置: '+', '.join(updates),flush=True)
