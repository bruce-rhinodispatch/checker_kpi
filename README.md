# how to install 

1.clone repository
```bash
git clone https://github.com/bruce-rhinodispatch/checker_kpi.git
```

2.install venv
```bash
sudo apt install python3-venv
```

3. create venv
```bash
python3 -m venv checker_kpi/venv
```

4. Go to project folder
```bash
cd checker-kpi
```

5.activate venv
```bash
source venv/bin/activate 
```

6.install requeriments
```bash
pip3 install -r requirements.txt
```

7. create db
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

8. create superuser
```bash
python3 manage.py createsuperuser
```

