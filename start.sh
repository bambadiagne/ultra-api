
if [ $DEBUG = "True" ]; then
    python3 app.py
else
    gunicorn -w 1 -b 0.0.0.0:5000 app:app
fi
