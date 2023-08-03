from flask import render_template, request, redirect
from app import dao, app, login
from flask_login import login_user, logout_user, current_user
from app.decorators import anonymous_user
from app.admin import *
from app.models import UserRole


app.add_url_rule('/', 'index', controller.index)
app.add_url_rule('/login/', 'login', controller.login_my_user, methods=['get','post'])
app.add_url_rule('/logout', 'logout', controller.logout_my_user)
app.add_url_rule('/register/', 'register', controller.register, methods=['get', 'post'])
app.add_url_rule('/api/admin/flights/new/', 'add-flight', controller.airports)
app.add_url_rule('/booking', 'booking', controller.booking)
app.add_url_rule('/api/search_booking', 'load-flight', controller.load_flights)
app.add_url_rule('/booking_staff', 'booking_staff', controller.booking_staff)
app.add_url_rule('/flight/<flight_id>', 'detail', controller.details)
app.add_url_rule('/search_booking', 'search_booking', controller.search_booking)
app.add_url_rule('/api/pay', 'pay', controller.pay)
app.add_url_rule('/pay', 'pay1', controller.pay1)
app.add_url_rule('/get_booking', 'get_booking', controller.get_booking, methods=['post'])



@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id=user_id)


if __name__ == "__main__":
    app.run(debug=True)


