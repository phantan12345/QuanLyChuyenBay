import random

from app.models import User, Profile, AirPlane, Seat, AirPort, AirLine, Flight, Flight_AirportMedium, \
    PlaneTicket, Regulation,FA_Regulation
from app import db
from flask_login import current_user
from sqlalchemy import func
import hashlib
from datetime import datetime
from sqlalchemy.sql import extract




def get_user_by_id(user_id):
    return User.query.get(user_id)


def check_login(username, password):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username.strip()),
                                 User.password.__eq__(password)).first()


def register(name, username, password):
    if name and username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        u = User(name=name, username=username.strip(), password=password)
        db.session.add(u)
        db.session.commit()

def check_profile(name,dob,email,phone):
    if name and dob and email and phone:
        p=Profile(id=random.randint(1,10),name=name,gender='nam',dob=dob,email=email,phone=phone ,isSupervisor=0)
        db.session.add(p)
        db.session.commit()


def load_airports():
    return AirPort.query.all()


def get_apm_by_flight_id(flight_id):
    return Flight_AirportMedium.query.filter(
        Flight_AirportMedium.flight_id.__eq__(flight_id)
    ).all()


def del_apm(flight_id, airport_id):
    apm = Flight_AirportMedium.query.filter(
        Flight_AirportMedium.flight_id.__eq__(flight_id),
        Flight_AirportMedium.airport_medium_id.__eq__(airport_id)
    ).first()
    db.session.delete(apm)
    db.session.commit()


def del_flight(flight_id):
    f = Flight.query.get(flight_id)
    db.session.delete(f)
    db.session.commit()


def take_time(str_date, format):
    default_date = datetime(1900, 1, 1)
    date = datetime.strptime(str_date, format)
    time = date - default_date
    return time


def get_regulation_time_by_id(id):
    date = Regulation.query.get(id)
    if date:
        return take_time(date.get_value(), "%H:%M:%S")
    else:
        return None


def check_time_flight(departing_at, arriving_at, regulation_id):
    duration = arriving_at - departing_at
    rt = get_regulation_time_by_id(regulation_id)
    if rt:
        if duration.total_seconds() > rt.total_seconds():
            msg = "success"
        else:
            msg = "Thời gian bay chưa đạt tối thiểu"
    else:
        msg = "Hiện chưa có quy định về thời gian bay tối thiểu"

    return msg


def check_plane_in_flight(departing_at, arriving_at, plane):
    planes = Flight.query.filter(Flight.plane_id.__eq__(plane)).all()
    if planes:
        for p in planes:
            if arriving_at < p.departing_at or p.arriving_at < departing_at:
                msg = "success"
            else:
                msg = "Máy bay đã có lịch bay trong khoảng thời gian này"
    else:
        msg = "success"

    return msg


def check_flight(id, name, departing_at, arriving_at, plane, regulation_id):
    if id and name and departing_at and arriving_at:
        flight = Flight.query.filter(Flight.id.__eq__(id.strip())).first()
        if flight:
            msg = "Mã chuyến bay đã tồn tại"
        else:
            msg = check_time_flight(departing_at, arriving_at, regulation_id)
            if msg == 'success':
                msg = check_plane_in_flight(departing_at, arriving_at, plane)
    else:
        msg = "Thông tin chuyến bay chưa được điền đầy đủ!"
    return msg


def save_flight(id, name, departing_at, arriving_at, plane, airline, fl_reg):
    al_id = AirLine.query.filter(AirLine.name.__eq__(airline)).first()
    f = Flight(id=id, name=name,
               departing_at=departing_at, arriving_at=arriving_at,
               plane_id=plane, airline_id=al_id.id)
    f.regulations.append(fl_reg)
    db.session.add(f)
    db.session.commit()


def update_flight(model, id, name, departing_at, arriving_at, plane, airline):
    al_id = AirLine.query.filter(AirLine.name.__eq__(airline)).first()
    model.id = id
    model.name = name
    model.departing_at = departing_at
    model.arriving_at = arriving_at
    model.plane_id = plane
    model.airline_id = al_id.id
    db.session.commit()


def check_time_stop(begin, finish, flight_id, list_regulation):
    rt_begin = get_regulation_time_by_id(list_regulation[0])
    rt_finish = get_regulation_time_by_id(list_regulation[1])

    stop_duration = finish - begin
    if rt_begin and rt_finish:
        if stop_duration.total_seconds() >= rt_begin.total_seconds() \
                and stop_duration.total_seconds() <= rt_finish.total_seconds():
            f = Flight.query.get(flight_id)
            if begin > f.departing_at and finish < f.arriving_at:
                check_duration_msg = 'success'
            else:
                check_duration_msg = 'Thời gian dừng không phù hợp với thời gian bay'
        else:
            check_duration_msg = 'Thời gian dừng không đúng quy định'
    else:
        check_duration_msg = 'Vui lòng thiết lập quy định về thời gian dừng tối thiểu và tối đa'

    return check_duration_msg


def check_airport_in_medium(airline, stop_airport, flight_id):
    al = AirLine.query.filter(AirLine.name.__eq__(airline)).first()
    ap = AirPort.query.filter(AirPort.name.__eq__(stop_airport)).first()
    if ap.id != al.from_airport_id and ap.id != al.to_airport_id:
        apm = Flight_AirportMedium.query.filter(
            Flight_AirportMedium.flight_id.__eq__(flight_id),
            Flight_AirportMedium.airport_medium_id.__eq__(ap.id)
        ).first()
        if apm:
            check_am_msg = 'Sân bay này đã được chọn làm trung gian. Vui lòng chọn sân bay khác!'
        else:
            check_am_msg = 'success'
    else:
        check_am_msg = 'Sân bay dừng đã thuộc tuyến bay'

    return check_am_msg


def check_stop_station(name, begin, finish, airline, stop_airport, flight_id, list_regulation):
    if name and begin and finish:
        check_am_msg = check_time_stop(begin, finish, flight_id, list_regulation)
        if check_am_msg == 'success':
            check_am_msg = check_airport_in_medium(airline, stop_airport, flight_id)
    else:
        check_am_msg = 'Thông tin trạm dừng chưa được điền đầy đủ'
    return check_am_msg


def save_airport_medium(name, min_stop, max_stop, description, flight_id, airport, list_reg):
    ap = AirPort.query.filter(AirPort.name.__eq__(airport)).first()
    apm = Flight_AirportMedium(name=name, stop_time_begin=min_stop, stop_time_finish=max_stop,
               description=description, flight_id=flight_id, airport_medium_id=ap.id)
    for r in list_reg:
        far = FA_Regulation(flight_id=flight_id, airport_id=ap.id, regulation_id=r)
        db.session.add(far)
    db.session.add(apm)
    db.session.commit()


def update_apm(model, name, stop_time_begin, stop_time_finish, description, flight_id, airport):
    ap = AirPort.query.filter(AirPort.name.__eq__(airport)).first()
    model.name = name
    model.stop_time_begin = stop_time_begin
    model.stop_time_finish = stop_time_finish
    model.description = description
    model.flight_id = flight_id
    model.airport_medium_id = ap.id
    db.session.commit()



def cart_stats(cart):
    total_amount, total_quantity = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }




def load_airlines():
    return AirLine.query.all()


def load_airplanes():
    return AirPlane.query.all()


def load_flights():
    return Flight.query.all()


def load_tickets():
    return PlaneTicket.query.all()


def load_from_airlines(airport_id=None, kw=None):
    query = AirLine.query.filter()
    if kw:
        query = query.filter(AirLine.name.contains(kw))

    return query.all()


def load_to_airlines(airport_id=None, kw=None):
    query = AirLine.query.filter()

    if airport_id:
        query = query.filter(AirLine.to_airport_id.__eq__(airport_id))

    if kw:
        query = query.filter(AirLine.name.contains(kw))

    return query.all()


def get_airport_by_id(airport_id):
    return AirPort.query.get(airport_id)


def get_airline_by_id(airline_id):
    return AirLine.query.get(airline_id)


def get_from_airport_by_id(from_airport_id):
    return AirLine.query.get(from_airport_id)


def get_to_airport_by_id(to_airport_id):
    return AirLine.query.get(to_airport_id)


def get_flight_by_id(flight_id):
    return Flight.query.get(flight_id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()







def seat(flight_id=None): #khach dky ghe thanh cong
    if flight_id:
        seats = Seat.query.filter(Seat.flight_id.__eq__(flight_id)).all()
        for s in seats:
            if not s.status:
                return s
    return None


def ts(flight_id=None):  # fligt - > air
    if flight_id:
        amountUsed = Seat.query.filter(Seat.flight_id.__eq__(flight_id),
                                       Seat.status.__eq__(True)).all()

    fl = AirPlane.query.get(Flight.query.get(flight_id).plane_id)
    return fl.total_seat - amountUsed


def save_receipt(cart):
    if cart:
        p = Profile(user=current_user)
        db.session.add(p)

        for c in cart.values():
            pt = PlaneTicket(rank=c['rank'], price=c['price'], seat_id=c['seat'],
                             place=c['from'] + c['to'], profile=p)
            db.session.add(pt)

        db.session.commit()


# def count_result_by_airline():
#     return db.session.query(AirPort.id, AirPort.location, func.count(AirLine.id)) \
#         .join(AirLine, AirLine.from_airport_id.__eq__(AirPort.id), isouter=True) \
#         .join(AirLine, AirLine.to_airport_id.__eq__(AirPort.id), isouter=True) \
#         .group_by(AirLine.id).order_by(AirLine.id).all()


def load_search_airport(kw=None, from_airport_id=None, to_airport_id=None):
    query = db.session.query(AirLine.id, AirLine.name, AirLine.from_airport_id, AirLine.to_airport_id) \
        .join(AirPort, AirPort.id.__eq__(AirLine.from_airport_id)) \
        .join(AirPort, AirPort.id__eq__(AirLine.to_airport_id))

    if kw:
        query = query.filter(AirPort.location.contains(kw))

    if from_airport_id:
        query = query.filter(AirPort.id.__eq__(from_airport_id))

    if to_airport_id:
        query = query.filter(AirPort.id.__eq__(to_airport_id))

    return query.all()


def statistic_revenue_follow_month(airline_name=None, date=None):
    stats = db.session.query(AirLine.id, AirLine.name, func.sum(PlaneTicket.price), func.count(Flight.id.distinct())) \
        .join(Flight, Flight.airline_id.__eq__(AirLine.id), isouter=True) \
        .join(PlaneTicket, PlaneTicket.flight_id.__eq__(Flight.id), isouter=True) \
        .group_by(AirLine.id, AirLine.name)

    if airline_name and date:
        date = datetime.strptime(date, "%Y-%m")
        stats = stats.filter(AirLine.name.contains(airline_name))
        stats = stats.filter(extract('year', PlaneTicket.date) == date.year,
                             extract('month', PlaneTicket.date) == date.month)

    return stats.all()