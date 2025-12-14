B站，强哥学编程
综合练习：单会话单智能体（学术问答智能体）全栈开发（deepseek辅助）
内容：
前端技术栈（PC浏览器）：
	HTML+CSS+TS（JS升级，Type Script）
	VUE3： 前端应用框架
	VITE：前端服务框架
	ElementPlus：元素组件
	Pinia：状态管理

后端技术栈（基于python）：
	FASTApi：基于python后端应用框架
	Uvicorn：后端服务框架（web服务/Restfull 服务）
	SQLAlchemy：ORM（对象关系映射）+SQLlite
	Pydantic：类型验证（python语言）
	langchain： agent 开发

起点：技术栈
终点：业务逻辑，状态和时序

前置条件，在windows：
	1. python
	2. anaconda
	3. node.js
	4. git

===============================
B站，强哥学编程
综合练习：单会话单智能体（学术问答智能体）全栈开发（deepseek辅助）
开发过程：
一. 后端开发：
1. 搭建conda开发环境：
	(base) C:\Users\xiaoq>conda env list
	(base) C:\Users\xiaoq>conda create -n py314-research-agent python=3.14
	conda activate py314-research-agent
2. 创建工作目录：
	(py314-research-agent) D:\ai-ide-workspace\research_agent>
3. 启动 code . 
4. 安装 python 包
	pip install fastapi
	pip install uvicorn
	pip install sqlalchemy
	pip install langchain langchain-community langchain-deepseek
	pip install arxiv langchain-arxiv
pip list
aiohappyeyeballs==2.6.1
aiohttp==3.13.2
aiosignal==1.4.0
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.0
attrs==25.4.0
certifi==2025.11.12
charset-normalizer==3.4.4
click==8.3.1
colorama==0.4.6
dataclasses-json==0.6.7
distro==1.9.0
fastapi==0.124.4
frozenlist==1.8.0
greenlet==3.3.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
httpx-sse==0.4.3
idna==3.11
jiter==0.12.0
jsonpatch==1.33
jsonpointer==3.0.0
langchain==1.1.3
langchain-classic==1.0.0
langchain-community==0.4.1
langchain-core==1.2.0
langchain-deepseek==1.0.1
langchain-openai==1.1.3
langchain-text-splitters==1.1.0
langgraph==1.0.5
langgraph-checkpoint==3.0.1
langgraph-prebuilt==1.0.5
langgraph-sdk==0.3.0
langsmith==0.4.59
marshmallow==3.26.1
multidict==6.7.0
mypy_extensions==1.1.0
numpy==2.3.5
openai==2.11.0
orjson==3.11.5
ormsgpack==1.12.0
packaging==25.0
propcache==0.4.1
pydantic==2.12.5
pydantic-settings==2.12.0
pydantic_core==2.41.5
python-dotenv==1.2.1
PyYAML==6.0.3
regex==2025.11.3
requests==2.32.5
requests-toolbelt==1.0.0
sniffio==1.3.1
SQLAlchemy==2.0.45
starlette==0.50.0
tenacity==9.1.2
tiktoken==0.12.0
tqdm==4.67.1
typing-inspect==0.9.0
typing-inspection==0.4.2
typing_extensions==4.15.0
urllib3==2.6.2
uuid_utils==0.12.0
uvicorn==0.38.0
xxhash==3.6.0
yarl==1.22.0
zstandard==0.25.0

目录：


运行：
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


前端：
D:\ai-ide-workspace\research_agent>npm create vue@latest frontend
D:\ai-ide-workspace\research_agent>cd frontend
D:\ai-ide-workspace\research_agent\frontend>npm install
D:\ai-ide-workspace\research_agent\frontend>npm install element-plus @element-plus/icons-vue
D:\ai-ide-workspace\research_agent\frontend>npm install axios
D:\ai-ide-workspace\research_agent\frontend>npm install pinia-plugin-persistedstate
D:\ai-ide-workspace\research_agent\frontend>npm install date-fns

