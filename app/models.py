import string
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, ForeignKey, DateTime, Enum, Text, subquery
from sqlalchemy.orm import relationship, backref
from app import db, app
from enum import Enum as UserEnum
from flask_login import UserMixin
import hashlib
from datetime import datetime, time, timedelta


class UserRole(UserEnum):
    USER = 1
    EMPLOYEE = 2
    ADMIN = 3


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now())
    user_role = Column(Enum(UserRole), default=UserRole.USER)

    def __str__(self):
        return str(self.id)


class Profile(db.Model):
    __tablename__ = 'profiles'

    serial = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(12), nullable=False)
    name = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=False)
    dob = Column(DateTime, nullable=False)
    email = Column(String(50), nullable=False)
    phone = Column(String(10), nullable=False)
    isSupervisor = Column(Boolean, default=False)

    def __str__(self):
        return str(self.id)


class AirPlane(db.Model):
    __tablename__ = 'airplanes'

    id = Column(String(10), primary_key=True)
    name = Column(String(50), nullable=False)
    manufacturer = Column(String(50), nullable=False)
    total_seat = Column(Integer, nullable=False)
    image = Column(String(100))

    def __str__(self):
        return str(self.id)


class AirPort(db.Model):
    __tablename__ = 'airports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    image = Column(String(100))
    location = Column(String(100), nullable=False)

    def __str__(self):
        return str(self.name)


class AirLine(db.Model):
    __tablename__ = 'airlines'

    id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)

    from_airport_id = Column(Integer, ForeignKey(AirPort.id, ondelete="CASCADE", onupdate="cascade"), nullable=False)
    to_airport_id = Column(Integer, ForeignKey(AirPort.id, ondelete="CASCADE"), nullable=False)

    from_airport = relationship("AirPort", foreign_keys=[from_airport_id], lazy=True,
                                passive_deletes=True, cascade="all, delete")
    to_airport = relationship("AirPort", foreign_keys=[to_airport_id], lazy=True,
                              passive_deletes=True, cascade="all, delete")

    def __str__(self):
        return str(self.name)


flight_regulation = db.Table('flight_regulation',
    Column('flight_id', String(10), ForeignKey('flights.id', ondelete="CASCADE", onupdate="cascade"), primary_key=True),
    Column('regulation_id', Integer, ForeignKey('regulations.id', ondelete="CASCADE", onupdate="cascade"), primary_key=True)
)


class Flight(db.Model):
    __tablename__ = 'flights'

    id = Column(String(10), primary_key=True)
    name = Column(String(50), nullable=False)
    departing_at = Column(DateTime, nullable=False)
    arriving_at = Column(DateTime, nullable=False)

    plane_id = (Column(String(10), ForeignKey(AirPlane.id, ondelete="CASCADE", onupdate="cascade"), nullable=False))
    airline_id = (Column(String(10), ForeignKey(AirLine.id, ondelete="CASCADE", onupdate="cascade"), nullable=False))
    planes = relationship("AirPlane", foreign_keys=[plane_id], lazy=True,
                          passive_deletes=True, cascade="all, delete")
    airlines = relationship("AirLine", foreign_keys=[airline_id], lazy=True,
                            passive_deletes=True, cascade="all, delete")

    regulations = relationship("Regulation", secondary=flight_regulation, lazy='subquery',
                            backref=backref('regulations', lazy=True), passive_deletes=True, cascade="all, delete")

    def __str__(self):
        return str(self.name)


class Seat(db.Model):
    __tablename__ = 'seats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    status = Column(Boolean, default=False)

    flight_id = Column(String(10), ForeignKey(Flight.id, ondelete="CASCADE", onupdate="cascade"), nullable=False)
    flights = relationship("Flight", foreign_keys=[flight_id], lazy=True,
                           passive_deletes=True, cascade="all, delete")

    def __str__(self):
        return str(self.id)


class FA_Regulation(db.Model):
    flight_id = Column(String(10), ForeignKey('flight_airport_mediums.flight_id', ondelete="CASCADE",
                            onupdate="cascade"), primary_key=True)
    airport_id = Column(Integer, ForeignKey('flight_airport_mediums.airport_medium_id', ondelete="CASCADE",
                            onupdate="cascade"), primary_key=True)
    regulation_id = Column(Integer, ForeignKey('regulations.id', ondelete="CASCADE",
                                                onupdate="cascade"), primary_key=True)

    flights = relationship("Flight_AirportMedium", foreign_keys=[flight_id], lazy='subquery',
                           passive_deletes=True, cascade="all, delete")
    airports = relationship("Flight_AirportMedium", foreign_keys=[airport_id], lazy='subquery',
                           passive_deletes=True, cascade="all, delete")
    regs = relationship("Regulation", foreign_keys=[regulation_id], lazy='subquery',
                        passive_deletes=True, cascade="all, delete")


class Flight_AirportMedium(db.Model):
    __tablename__ = 'flight_airport_mediums'

    name = Column(String(50), nullable=False)
    stop_time_begin = Column(DateTime, nullable=False)
    stop_time_finish = Column(DateTime, nullable=False)
    description = Column(Text)

    flight_id = Column(String(10), ForeignKey(Flight.id, ondelete="CASCADE", onupdate="cascade"), primary_key=True)
    airport_medium_id = Column(Integer, ForeignKey(AirPort.id, ondelete="CASCADE", onupdate="cascade"), primary_key=True)
    flights = relationship("Flight", foreign_keys=[flight_id], lazy=True,
                           passive_deletes=True, cascade="all, delete")
    airports = relationship("AirPort", foreign_keys=[airport_medium_id], lazy=True,
                            passive_deletes=True, cascade="all, delete")

    def __str__(self):
        return str(self.name)


ticket_regulation = db.Table('ticket_regulation',
    Column('ticket_id', Integer, ForeignKey('tickets.id', ondelete="CASCADE", onupdate="cascade"), primary_key=True),
    Column('regulation_id', Integer, ForeignKey('regulations.id', ondelete="CASCADE", onupdate="cascade"), primary_key=True)
)


class PlaneTicket(db.Model):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rank = Column(Integer, nullable=False)
    price = Column(DECIMAL(18, 2), nullable=False)
    date = Column(DateTime, default=datetime.now())

    place = Column(Integer, ForeignKey(AirPort.id, ondelete="CASCADE", onupdate="cascade"))
    profile_id = (Column(Integer, ForeignKey(Profile.serial, ondelete="CASCADE", onupdate="cascade"), nullable=False))
    flight_id = (Column(String(10), ForeignKey(Flight.id, ondelete="CASCADE", onupdate="cascade"), nullable=False))
    seat_id = (Column(Integer, ForeignKey(Seat.id, ondelete="CASCADE", onupdate="cascade"), nullable=False))
    user_id = (Column(Integer, ForeignKey(User.id, ondelete="CASCADE", onupdate="cascade")))

    places = relationship("AirPort", foreign_keys=[place], lazy=True,
                          cascade="all, delete", passive_deletes=True)
    profiles = relationship("Profile", foreign_keys=[profile_id], lazy=True,
                            cascade="all, delete", passive_deletes=True)
    flights = relationship("Flight", foreign_keys=[flight_id], lazy=True,
                           cascade="all, delete", passive_deletes=True)
    seats = relationship("Seat", foreign_keys=[seat_id], lazy=True, uselist=False,
                         cascade="all, delete", passive_deletes=True)
    users = relationship("User", foreign_keys=[user_id], lazy=True,
                         cascade="all, delete", passive_deletes=True)

    def __str__(self):
        return str(self.id)


class Regulation(db.Model):
    __tablename__ = 'regulations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    value = Column(String(50), nullable=False)
    description = Column(Text)

    tickets = relationship("PlaneTicket", secondary=ticket_regulation, lazy='subquery',
                        backref=backref('tickets', lazy=True), passive_deletes=True, cascade="all, delete")

    def __str__(self):
        return str(self.id)

    def get_value(self):
        return self.value


if __name__ == '__main__':
    with app.app_context():

        db.drop_all()
        db.create_all()

        password = str(hashlib.md5('1'.encode('utf-8')).hexdigest())
        u1 = User(name='Mai', username='mai', password=password,
                  user_role=UserRole.USER)
        u2 = User(name='Son', username='son', password=password,
                  user_role=UserRole.EMPLOYEE)
        u3 = User(name='Tan', username='tan ', password=password,
                  user_role=UserRole.ADMIN)
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        p1 = Profile(id='01231', name='Nguyen Van An', gender='nam', dob=datetime(2002,1,1), email='an1100@gmail.com',
                     phone='0176448394')
        p2 = Profile(id='01232', name='Le Thi Binh', gender='nu', dob=datetime(2001, 11, 6),
        email='binh1211@gmail.com',
                     phone='0176640394')
        p3 = Profile(id='01233', name='Tran Van Dong', gender='nam', dob=datetime(2000, 4, 17),
                     email='dong1100@gmail.com',
                     phone='0176470094', isSupervisor=True)
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        pl1 = AirPlane(id='MB1', name='May bay 1', manufacturer='VN AirLine', total_seat=60)
        pl2 = AirPlane(id='MB2', name='May bay 2', manufacturer='VN AirLine', total_seat=70)
        pl3 = AirPlane(id='MB3', name='May bay 3', manufacturer='VN AirLine', total_seat=65)
        db.session.add_all([pl1, pl2, pl3])
        db.session.commit()


        sb1 = AirPort(name='Sân bay Nội Bài', location='Hà Nội',
                      image='https://res.cloudinary.com/dahppd9es/image/upload/v1670266574/Airport_Location/HaNoi_wkzzg5.jpg')
        sb2 = AirPort(name='Sân bay Tân Sơn Nhất', location='Hồ Chí Minh',
                      image='https://res.cloudinary.com/dahppd9es/image/upload/v1670266575/Airport_Location/HCM_jpkw5e.jpg')
        sb3 = AirPort(name='Sân bay Phù Cát', location='Bình Định',
                      image='https://res.cloudinary.com/dahppd9es/image/upload/v1670266574/Airport_Location/BinhDinh_c6yrif.jpg')
        sb4 = AirPort(name='Sân bay Narita', location='Nhật Bản',
                      image='https://res.cloudinary.com/dahppd9es/image/upload/v1670266739/Airport_Location/NhatBan_fzo3qw.jpg')
        sb5 = AirPort(name='Sân bay Bangkok', location='Thái Lan',
                      image='https://res.cloudinary.com/dahppd9es/image/upload/v1670266384/Airport_Location/ThaiLan_k533hb.jpg')
        db.session.add_all([sb1, sb2, sb3, sb4, sb5])
        db.session.commit()

        al1 = AirLine(id='1', name='Hà Nội - Hồ Chí Minh', from_airport_id='1', to_airport_id='2')
        al2 = AirLine(id='2', name='Hà Nội - Bình Định', from_airport_id='1', to_airport_id='3')
        al3 = AirLine(id='3', name='Bình Định - Hồ Chí Minh', from_airport_id='3', to_airport_id='2')
        al4 = AirLine(id='4', name='Hồ Chí Minh - Nhật Bản', from_airport_id='2', to_airport_id='4')
        al5 = AirLine(id='5', name='Hồ Chí Minh - Thái Lan', from_airport_id='2', to_airport_id='5')
        db.session.add_all([al1, al2, al3, al4, al5])
        db.session.commit()

        f1 = Flight(id='CB1', name='Chuyến bay 001'  , departing_at=datetime(2022, 12, 1, 13, 00, 00),
                    arriving_at=datetime(2022, 12, 1, 14, 00, 00), plane_id='MB1', airline_id='1')
        f2 = Flight(id='CB2', name='Chuyến bay 002'   , departing_at=datetime(2022, 12, 1, 18, 00, 00),
                    arriving_at=datetime(2022, 12, 1, 19, 00, 00), plane_id='MB2', airline_id='2')
        f3 = Flight(id='CB3', name='Chuyến bay 003'   ,departing_at=datetime(2022, 12, 1, 9, 00, 00),
                    arriving_at=datetime(2022, 12, 1, 9, 50, 00), plane_id='MB3', airline_id='3')
        f4 = Flight(id='CB4', name='Chuyến bay 004'   ,departing_at=datetime(2022, 12, 11, 9, 00, 00),
                    arriving_at=datetime(2022, 12, 11, 18, 50, 00), plane_id='MB2', airline_id='3')
        db.session.add_all([f1, f2, f3, f4])
        db.session.commit()

        s1 = Seat(name='Ghế 1', flight_id='CB1')
        s2 = Seat(name='Ghế 2', flight_id='CB2')
        s3 = Seat(name='Ghế 3', flight_id='CB3')
        db.session.add_all([s1, s2, s3])
        db.session.commit()

        fam1 = Flight_AirportMedium(name='Tram dung 1', stop_time_begin=datetime(2022, 12, 1, 13, 10, 00),
                                    stop_time_finish=datetime(2022, 12, 1, 13, 35, 00),
                                    description="CB được nghỉ tại đây 20 phút", flight_id='CB1',
                                    airport_medium_id='3')
        fam2 = Flight_AirportMedium(name='Tram dung 1', stop_time_begin=datetime(2022, 12, 1, 13, 10, 00),
                                    stop_time_finish=datetime(2022, 12, 1, 13, 35, 00),
                                    description="CB được nghỉ tại đây 20 phút", flight_id='CB2',
                                    airport_medium_id='3')
        db.session.add_all([fam1, fam2])
        db.session.commit()

        t1 = PlaneTicket(rank='2', price=1800000, place="1", profile_id='1',
                         flight_id='CB1', seat_id=1, user_id='2')
        t2 = PlaneTicket(rank='1', price=2000000, place="1", profile_id='2',
                         flight_id='CB2', seat_id=1, user_id='2')
        t3 = PlaneTicket(rank='1', price=1400000, place="3", profile_id='3',
                         flight_id='CB3', seat_id=2, user_id='2')
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        g1 = Regulation(name='book_time', value='12:00:00',
                        description='Thời gian đặt vé trước 12h lúc chuyến bay khởi hành')
        g2 = Regulation(name='sale_time', value='4:00:00',
                        description='Thời gian bán vé trước 4h lúc chuyến bay khởi hành')
        g3 = Regulation(name='1', value='300000',
                        description='Vé hạng 1 có đơn giá là 300.000 VND')
        g4 = Regulation(name='2', value='200000',
                        description='Vé hạng 2 có đơn giá là 200.000 VND')
        g5 = Regulation(name='duration', value='00:30:00',
                        description='Thời gian bay tối thiểu là 30 phút')
        g6 = Regulation(name='min_stop', value='00:20:00',
                        description='Thời gian máy bay được dừng tối thiểu 20 phút')
        g7 = Regulation(name='max_stop', value='00:30:00',
                        description='Thời gian máy bay được dừng tối đa 30 phút')
        db.session.add_all([g1, g2, g3, g4, g5, g6, g7])
        db.session.commit()

        f3.regulations.append(g5)
        g3.tickets.append(t1)
        far = FA_Regulation(flight_id=fam1.flight_id, airport_id=fam1.airport_medium_id, regulation_id=g6.id)
        db.session.add(far)
        db.session.commit()