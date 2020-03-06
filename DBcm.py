import mysql.connector #подключаем драйвер MySQL connector

class ConnectionError(Exception): #создаем свое исключение используя класс Exception
    pass #pass означает отсутствие нового кода, а не пустой класс. Идет наследование встроенноого класса Exception

class CredentialsError(Exception):
    pass

class SQLError(Exception):
    pass

class UseDatabase:
    def __init__(self, config: dict) -> None: #метод init принимает единственный словарь config
        self.configuration = config   #значение аргумента config присваивается атрибуту  configuration
    def __enter__(self) -> 'cursor':   #метод обеспечивает настройку объекта перед началом выполнения инструкции with
        try:
            self.conn = mysql.connector.connect(**self.configuration)
            self.cursor = self.conn.cursor()
        #к переменным  conn и  cursor добавлен self для их сохранностипо завершении метода, так как они нужны в exit
            return self.cursor #вернуть курсор
        except mysql.connector.errors.InterfaceError as err:
            raise ConnectionError(err)   #возбуждаем собственное исключение
        except mysql.connector.errors.ProgrammingError as err:
            raise CredentialsError(err)   #возбуждаем собственное исключение для обработки любых проблем с регистрацией
####!!!!!! Если исключение возникнет внутри диспетчера контекста, и не будет перехвачено, то оно будет переданоно в метод __exit__
    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:  # эти 3 аргумента для обработки исключений, когда что то не так внутри блока with
        #тип сключения, значение исключения и трассировка стека
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        #записываем в базу все значения и закрываем курсор и соединение
        if exc_type is mysql.connector.errors.ProgrammingError: #если возникло ProgrammingError, возбудить SQLError
            raise SQLError(exc_value)
        elif exc_type:  #повторно возбуждает любое исключение, которое может возникнуть
            raise exc_type(exc_value)
