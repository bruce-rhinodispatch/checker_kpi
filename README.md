# how to install 

1. Сlone repository
```bash
git clone https://github.com/bruce-rhinodispatch/checker_kpi.git
```

2. Go to project folder
```bash
cd checker-kpi
```

3.Install venv
```bash
sudo apt install python3-venv
```

4. Create venv
```bash
python3 -m venv venv
```

5. Activate venv
```bash
source venv/bin/activate 
```

6. Install requeriments
```bash
pip3 install -r requirements.txt
```

7. Create/update  db
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

8. Run scrapyrt
```bash
cd checker_kpi/sylectus_spider/sylectus_spider 
scrapyrt
```

# update

1. Go to project folder
```bash
cd checker-kpi
```
2. Pull  changes
```bash
git pull 
```

3. Activate venv
```bash
source venv/bin/activate 
```

4. Install requeriments
```bash
pip3 install -r requirements.txt
```

5. Update  db
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```
