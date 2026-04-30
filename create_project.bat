@echo off
echo 正在创建项目目录结构...

mkdir app\core 2>nul
mkdir app\models 2>nul
mkdir app\schemas 2>nul
mkdir app\crud 2>nul
mkdir app\api\v1 2>nul

cd. > app\__init__.py
cd. > app\main.py

cd. > app\core\__init__.py
cd. > app\core\config.py
cd. > app\core\database.py
cd. > app\core\security.py
cd. > app\core\dependencies.py

cd. > app\models\__init__.py
cd. > app\models\user.py

cd. > app\schemas\__init__.py
cd. > app\schemas\user.py
cd. > app\schemas\token.py

cd. > app\crud\__init__.py
cd. > app\crud\base.py
cd. > app\crud\user.py

cd. > app\api\__init__.py
cd. > app\api\deps.py

cd. > app\api\v1\__init__.py
cd. > app\api\v1\auth.py

cd. > .env
cd. > .gitignore
cd. > requirements.txt

echo.
echo ============================================
echo  项目结构创建成功！
echo ============================================
echo.
echo 下一步：
echo 1. 激活虚拟环境: venv\Scripts\activate
echo 2. 安装依赖: pip install -r requirements.txt
echo 3. 启动服务: uvicorn app.main:app --reload
echo.

pause