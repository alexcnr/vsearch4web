from flask import Flask, render_template, request, escape, session #импортируем класс Flask из модуля flask
#request - доступ к переданным данным, заменяем данные в функции , переданными данными
#render_template - принимает имя шаблона и возвращает строку с разметкой HTML
#redirect - возможность перенаправления из фреймворка Flask
from flask import copy_current_request_context
from vsearch import search4letters
from DBcm import UseDatabase, ConnectionError, CredentialsError  #импорт класса UseDatabase из модуля DBcm, а также собственное исключение
from checker import check_logged_in
from threading import Thread #для многопоточности
from time import sleep  #$чтобы моделировать задержку
from config import dbconfig
#app = Flask(__name__) #создание объекта типа Flask  и присвоим его переменной app
#__name__ - определяет текущее активное пространство имен

app = Flask(__name__)
app.config['dbconfig'] = dbconfig
#app.secret_key = secret_key

# дальше добавляем словарь с параметрами в внутренний словарь flask (app.config)
#app.config['dbconfig'] = {'host': '127.0.0.1',   #определим параметры соединения
#                        'user': 'vsearch2',
#                        'password': 'pass',   ##// ключу password присваивается пароль, который указали для доступа к БД
#                        'database': 'vsearchlogDB', }    ## //имя БД vsearchlogDB присвоено ключу database
@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True  #значение true присваивается ключу 'logged_in' в словаре session, значит браузер вошел в систему
    return 'You are now logged in'


@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')  #удаляем ключ 'logged_in' из словаря session
    return 'You are NOT logged in'

@app.route('/search4', methods=['POST'])
def do_search() -> 'html':  #теперь функция возвращает html
    @copy_current_request_context  #декоратор который гарантирует что HTTP запрос который активен в момент вызова функции останется активным, когда функция запустится в отдельном потоке
    def log_request(req: 'flask_request', res: str) -> None:  #none значит нет возвращаемого значения
        sleep(1) #моделируем задержку
#функция используект диспетчер контекста UseDataBase для записи в базу данных
# функция записывает данные и заставляет приложение ждать пока это не завершиться!!!!!!!!!!!!!!!!!, ЦЕЛЬ - запустить параллельно осноновному приложению этот процесс каждый раз когда происходит вызов этой функции
        with UseDatabase(app.config['dbconfig']) as cursor:
        #используем диспетчер контекста UseDatabase, передав ему настройки из app.config
            _SQL = """insert into log
           (phrase, letters, ip, browser_string, results)
           values
           (%s, %s, %s, %s, %s)"""      # //использование меток заполнителей
# // используем запрос insert и добавим данные в таблицу
            cursor.execute(_SQL, (req.form ['phrase'],
                          req.form['letters'],
                          req.remote_addr,
                          req.user_agent.browser,    #извлекается только название браузера
                          res, ))
##    в этой точке работа приложения приостанавливается пока БД не закончит свои дела
# если эта функция не дождется аока SELECT вернет записи БД, то код после cursor.execute завершиться с ошибкой
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results:'
    results = str(search4letters(phrase, letters))
    try:
        t=Thread(target = log_request, args=(request, results))# параллельный сеанс запускаем
        t.start() # запуск потока
##        log_request(request, results) #несмотря на ошибки приложение не покажет пользователю ошибку
    except Exception as err:  #присвоим err любое исключение (оштибку)
        print('*****Loging failed with this error', str(err))
    return render_template( 'results.html',  #отображаем шаблон results.html, который ждет значения 4 аргументов
                            the_phrase = phrase,
                            the_letters = letters,
                            the_title = title,
                            the_results = results,
)

#связываем каждую переменную с соответствующим аргументом
@app.route('/')   #route это встроенный декоратор функции
@app.route('/entry')
def entry_page() -> 'html':  #функция entry_page связана с 2 URL и нет необходимости использовать redirect
    return render_template('entry.html',
                            the_title='Welcome to search4letters on the web!')

@app.route('/viewlog')   #добавили новый url для журнала лога
@check_logged_in
def view_the_log() -> 'html': # извлекает данные из текстого файла vsearch.log, превращает их в список списков и передает его в шаблон viewlog.html
    #эту функцию вызывает Flask от нашего имени
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
        #используем диспетчер контекста UseDatabase, передав ему настройки из app.config и защищаем вызов диспетчера контекста с помощью try
            _SQL = """select phrase, letters, ip, browser_string, results
                  from log """ #данные из таблицы возвращаются в Python в виде списка кортежей
            cursor.execute(_SQL) # передать запрос в переменной SQL серверу для выполнения
            contents = cursor.fetchall() # получить все записи полученные от MySQL
        titles = ('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results') #создали кортеж заголовков и добавили все в него
        return render_template('viewlog.html',
                            the_totle='View Log',
                            the_row_titles=titles,
                            the_data=contents,)
    except ConnectionError as err: #это и следующее исключения возбуждаются внутри __enter__, когда они появляются, то  блок кода внутри with не выполняется
        print('Is your database switched on? Error:', str(err))
    except CredentialsError as err: #отслеживаем момент когда код использует неправильное имя пользователя или пароль для MySQL
        print('User-id/Password issues. Error:', str(err))
    except SQLError as err:
        print('Is your query correct? Error:', str(err))
    except Exception as err:
        print('Something went wrong:', str(err))
    return 'Error'


app.secret_key = 'YouWillNeverGuess'  #инициализируем куки этим секретным ключем

if __name__ == '__main__':
    app.run(debug=True) # строка предлагает объекту Flask в переменной app запустить веб сервер вызывая метод run

#view_the_log  и log_request обе функции  используют диспетчер контекста для выполнения SQL запросов.
# log_request - записывает результаты в базу данных, а view_the_log читает их