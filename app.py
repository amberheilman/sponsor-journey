from logging.config import dictConfig
import os
import uuid

import flask
from flask import Flask
from flask import render_template
import psycopg2
import waitress


version = '1.0.0'
app = Flask(__name__)
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})
app.conn = psycopg2.connect(os.environ['DATABASE_URL'])  # TODO: reconnect logic
SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost')
SCHEME = os.environ.get('SCHEME', 'https')


INSERT_SPONSORSHIP_EMAIL = ("INSERT INTO sponsorship_emails"
                            "            (id, sponsorship_id, "
                            "             contact_email, adoption_status)"
                            "     VALUES (%s, %s, %s, 'adoptable')")
SELECT_SPONSORSHIP_CAT = ("SELECT cat_name, cat_img FROM sponsorships"
                          " WHERE id=%s")


def execute_sql(*sql_dict, raise_error=None, cursor_factory=None):
    result = None
    error = None
    app.logger.debug('Running query %r', sql_dict)
    try:
        with app.conn.cursor(cursor_factory=cursor_factory) as cur:
            for sql in sql_dict:
                if sql.get('values'):
                    cur.execute(sql['sql'], sql['values'])
                else:
                    cur.execute(sql['sql'])
                if sql.get('fetchall') is True:
                    result = cur.fetchall()
                elif sql.get('fetchone') is True:
                    result = cur.fetchone()
                else:
                    pass
            cur.close()
        app.conn.commit()
    except psycopg2.Error as e:
        error = e
        app.conn.rollback()
        app.logger.exception('Encountered db error sql: %r', sql_dict)
    except Exception as e:
        error = e
        app.conn.rollback()
        app.logger.exception('Encountered unknown error sql: %r', sql_dict)
    if raise_error and isinstance(error, raise_error):
        raise error
    return result


@app.route("/<sponsor_id>", methods=['GET', 'POST'])
def signup(sponsor_id):
    cat = execute_sql({'sql': SELECT_SPONSORSHIP_CAT,
                       'values': [sponsor_id],
                       'fetchone': True})
    if not cat:
        return render_template('fail.html')

    if flask.request.method == 'GET':
        return render_template('signup.html', name=cat[0], img=cat[1])
    if flask.request.method == 'POST':
        email = flask.request.form.get('email')
        try:
            execute_sql(
                {'sql': INSERT_SPONSORSHIP_EMAIL,
                 'values': [str(uuid.uuid4()), sponsor_id, email]},
                raise_error=psycopg2.errors.InvalidTextRepresentation)
        except psycopg2.errors.InvalidTextRepresentation:
            return render_template('fail.html')

        app.logger.info(cat)
        return render_template('thank-you.html', name=cat[0], img=cat[1])


if __name__ == "__main__":
    waitress.serve(app, port=os.environ.get('PORT', 5000))
