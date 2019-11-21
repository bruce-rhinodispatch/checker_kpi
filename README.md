# how to install 

1.clone repository
```bash
git clone https://github.com/bruce-rhinodispatch/checker_kpi.git
```

2. Go to project folder
```bash
cd checker-kpi
```

3.install venv
```bash
sudo apt install python3-venv
```

4. create venv
```bash
python3 -m venv venv
```

5.activate venv
```bash
source venv/bin/activate 
```

6.install requeriments
```bash
pip3 install -r requirements.txt
```

7. create/update  db
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

8. run scrapyrt
```bash
cd checker_kpi/sylectus_spider/sylectus_spider 
scrapyrt
```

# update

1. Go to project folder
```bash
cd checker-kpi
```
2. pull  changes
```bash
git pull 
```

3.activate venv
```bash
source venv/bin/activate 
```

4.install requeriments
```bash
pip3 install -r requirements.txt
```

5. update  db
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```
