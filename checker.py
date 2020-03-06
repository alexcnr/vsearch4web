#-------------------------------------------------------------------------------
# Name:        checker.py
# Purpose:  ДЕКОРАТОР!!!!!!
#-------------------------------------------------------------------------------

from flask import session
from functools import wraps

def check_logged_in(func:object):
    @wraps(func) #декорируем функцию wrapper с помощью декоратора wraps, передаем функцию func как аргумент
    def wrapper(*args, **kwargs ):  #  вложенная функция не только вызывает декорируемую функцию, но и "обертывает" вызов дополнительным кодом
        if 'logged_in' in session:   #код проверяет наличие ключа  'logged_in' в словаре session
            return func(*args, **kwargs )    #
        return 'You are NOT logged in'  # если пользователь не выполнил вход, то декорируемая функция не вызывается
    return wrapper   #возвращаем вложенную функцию



