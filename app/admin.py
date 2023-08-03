from decimal import Decimal

from flask import redirect, url_for, request, flash
from flask_admin import Admin, expose, BaseView
from flask_admin.babel import gettext, ngettext
from flask_admin.helpers import get_redirect_target, flash_errors
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_login import current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, DateTimeLocalField
from wtforms.validators import InputRequired, Length

from app import dao, controller

from app.models import *
from flask_admin.contrib.sqla import ModelView
from app import app, db

admin = Admin(app=app, name="ADMINISTRATOR", template_mode="bootstrap4")


class Base_View(ModelView):
    column_display_pk = True
    can_view_details = True
    can_export = True
    # edit_modal = True
    page_size = 10


class AuthenticatedFlight(Base_View):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.EMPLOYEE \
               or current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedModelView(Base_View):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class RegulationView(AuthenticatedModelView):
    details_modal = True
    edit_modal = True
    can_delete = False
    form_excluded_columns = ['regulations', 'tickets']
    column_filters = ['name', 'description']
    column_searchable_list = ['name', 'description']
    column_labels = {
        'id': 'ID',
        'name': 'Tên quy định',
        'value': 'Giá trị',
        'description': 'Mô tả'
    }


class FlightForm(FlaskForm):
    id = StringField(name="id", validators=[InputRequired(), Length(max=10)])
    name = StringField(name="name", validators=[InputRequired(), Length(max=50)])
    departing_at = DateTimeLocalField(name="departing_at", format="%Y-%m-%dT%H:%M",
                                      validators=[InputRequired()])
    arriving_at = DateTimeLocalField(name="arriving_at", format="%Y-%m-%dT%H:%M",
                                     validators=[InputRequired()])
    planes = SelectField('planes', choices=[])
    airlines = SelectField('airlines', choices=[])


class FlightManagementView(AuthenticatedFlight):
    column_filters = ['name', 'id']
    column_searchable_list = ['name', 'id']
    column_labels = {
        'id': 'Mã chuyến bay',
        'name': 'Tên chuyến bay',
        'departing_at': 'Thời gian khởi hành',
        'arriving_at': 'Thời gian đến',
        'planes': 'Số hiệu máy bay',
        'airlines': 'Tuyến bay'
    }

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)

        sts_msg = ''
        am_msg = ''
        form = FlightForm()

        list_regulation = [5]
        list_stop_regulation = [6, 7]

        form.planes.choices = [p.id for p in AirPlane.query.all()]
        form.airlines.choices = [a.name for a in AirLine.query.all()]

        if request.method == "POST":
            id = form.id.data
            name = form.name.data
            departing_at = form.departing_at.data
            arriving_at = form.arriving_at.data
            plane = form.planes.data
            airline = form.airlines.data

            sts_msg = dao.check_flight(id, name, departing_at, arriving_at, plane, list_regulation[0])

            if sts_msg == 'success':
                try:
                    reg = Regulation.query.get(list_regulation[0])
                    dao.save_flight(id, name, departing_at, arriving_at, plane, airline, reg)
                except:
                    sts_msg = 'Đã có lỗi xảy ra khi lưu chuyến bay! Vui lòng quay lại sau!'

                if 'isMedium' in request.form:
                    if 'number' in request.form:
                        num = int(request.form['number'])
                        for i in range(num):
                            str_name = "name-stop-" + str(i)
                            str_stb = "stop-time-begin-" + str(i)
                            str_stf = "stop-time-finish-" + str(i)
                            str_des = "description-" + str(i)
                            str_ap = "form-select-" + str(i)

                            am_name = request.form[str_name]
                            am_stb = datetime.strptime(request.form[str_stb], "%Y-%m-%dT%H:%M")
                            am_stf = datetime.strptime(request.form[str_stf], "%Y-%m-%dT%H:%M")
                            am_des = request.form[str_des]
                            am_ap = request.form[str_ap]
                            am_msg = dao.check_stop_station(am_name, am_stb,
                                                            am_stf, airline,
                                                            am_ap, id, list_stop_regulation)
                            if am_msg == 'success':
                                try:
                                    dao.save_airport_medium(am_name, am_stb,
                                                            am_stf, am_des,
                                                            id, am_ap, list_stop_regulation)
                                except:
                                    dao.del_flight(id)
                                    am_msg = 'Đã có lỗi xảy ra khi lưu sân bay trung gian! Vui lòng quay lại sau!'
                            else:
                                dao.del_flight(id)
                                am_msg = am_msg

                form.id.data = ""
                form.name.data = ""

        return self.render('admin/flight.html', form=form, list_regulation=list_regulation,
                           sts_msg=sts_msg, am_msg=am_msg,
                           list_stop_regulation=list_stop_regulation, return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        sts_msg = ''
        am_msg = ''
        am_edit_msg = ''

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        old_model = model
        old_airline = old_model.airlines.name
        form = FlightForm(obj=model)
        medium_list = []

        form.planes.choices = [p.id for p in AirPlane.query.all()]
        form.airlines.choices = [a.name for a in AirLine.query.all()]

        for apm in dao.get_apm_by_flight_id(id):
            medium_list.append(apm)

        medium_num = len(medium_list)

        fl_reg = [5]
        stop_reg = [6, 7]

        if request.method == "POST":
            f_id = form.id.data
            name = form.name.data
            departing_at = form.departing_at.data
            arriving_at = form.arriving_at.data
            plane = form.planes.data
            airline = form.airlines.data

            sts_msg = 'success'

            if departing_at != model.departing_at or arriving_at != model.arriving_at:
                sts_msg = dao.check_time_flight(departing_at, arriving_at, fl_reg[0])

            if plane != model.plane_id:
                sts_msg = dao.check_plane_in_flight(departing_at, arriving_at, plane)

            if f_id != model.id and Flight.query.filter(Flight.id.__eq__(f_id.strip())).first():
                sts_msg = "Mã chuyến bay đã tồn tại! Vui lòng đổi sang nội dung khác!"

            if sts_msg == 'success':
                try:
                    dao.update_flight(model, f_id, name, departing_at, arriving_at, plane, airline)
                except:
                    sts_msg = 'Đã có lỗi xảy ra khi cập nhật chuyến bay! Vui lòng quay lại sau!'

                medium_list = []
                for apm in dao.get_apm_by_flight_id(model.id):
                    medium_list.append(apm)
                medium_num = len(medium_list)

                if medium_num > 0:
                    for i in range(medium_num):
                        str_del_am = "del-" + str(i)

                        if str_del_am in request.form:
                            dao.del_apm(medium_list[i].flight_id, medium_list[i].airport_medium_id)
                            return redirect(self.get_url('.edit_view', id=self.get_pk_value(model)))
                        else:
                            str_edit_name = "ns-" + str(i)
                            str_edit_stb = "stb-" + str(i)
                            str_edit_stf = "stf-" + str(i)
                            str_edit_des = "d-" + str(i)
                            str_edit_ap = "form-edit-select-" + str(i)
                            am_edit_name = request.form[str_edit_name]
                            am_edit_stb = datetime.strptime(request.form[str_edit_stb], "%Y-%m-%dT%H:%M")
                            am_edit_stf = datetime.strptime(request.form[str_edit_stf], "%Y-%m-%dT%H:%M")
                            am_edit_des = request.form[str_edit_des]
                            am_edit_ap = request.form[str_edit_ap]

                            am_edit_msg = 'success'

                            if am_edit_stb != medium_list[i].stop_time_begin or \
                                    am_edit_stf != medium_list[i].stop_time_finish:
                                am_edit_msg = dao.check_time_stop(am_edit_stb, am_edit_stf, model.id, stop_reg)

                            if am_edit_ap != medium_list[i].airports.name or airline != old_airline:
                                am_edit_msg = dao.check_airport_in_medium(airline, am_edit_ap, model.id)

                            if am_edit_msg == 'success':
                                try:
                                    dao.update_apm(
                                        medium_list[i], am_edit_name, am_edit_stb,
                                        am_edit_stf, am_edit_des, f_id, am_edit_ap
                                    )
                                except:
                                    dao.update_flight(model, old_model.id, old_model.name,
                                                      old_model.departing_at, old_model.arriving_at,
                                                      old_model.plane_id, old_airline)
                                    am_edit_msg = 'Đã có lỗi xảy ra khi cập nhật trạm dừng! Vui lòng quay lại sau!'
                            else:
                                try:
                                    dao.update_flight(model, old_model.id, old_model.name,
                                                      old_model.departing_at, old_model.arriving_at,
                                                      old_model.plane_id, old_airline)
                                except:
                                    sts_msg = 'Đã có lỗi xảy ra khi cập nhật chuyến bay! Vui lòng quay lại sau!'
                                am_edit_msg = am_edit_msg

                if 'isMedium' in request.form:
                    if 'number' in request.form:
                        num = int(request.form['number'])
                        for i in range(num):
                            str_name = "name-stop-" + str(i)
                            str_stb = "stop-time-begin-" + str(i)
                            str_stf = "stop-time-finish-" + str(i)
                            str_des = "description-" + str(i)
                            str_ap = "form-select-" + str(i)

                            am_name = request.form[str_name]
                            am_stb = datetime.strptime(request.form[str_stb], "%Y-%m-%dT%H:%M")
                            am_stf = datetime.strptime(request.form[str_stf], "%Y-%m-%dT%H:%M")
                            am_des = request.form[str_des]
                            am_ap = request.form[str_ap]
                            am_msg = dao.check_stop_station(am_name, am_stb, am_stf, airline,
                                                            am_ap, model.id, stop_reg)
                            if am_msg == 'success':
                                try:
                                    dao.save_airport_medium(am_name, am_stb,
                                                            am_stf, am_des,
                                                            model.id, am_ap, stop_reg)
                                except:
                                    dao.update_flight(model, old_model.id, old_model.name,
                                                      old_model.departing_at, old_model.arriving_at,
                                                      old_model.plane_id, old_airline)
                                    am_msg = 'Đã có lỗi xảy ra khi lưu trạm dừng! Vui lòng quay lại sau!'
                            else:
                                dao.update_flight(model, old_model.id, old_model.name,
                                                  old_model.departing_at, old_model.arriving_at,
                                                  old_model.plane_id, old_airline)
                                am_msg = am_msg

            if sts_msg == 'success':
                if am_edit_msg == 'success' or am_edit_msg == '':
                    if am_msg == 'success' or am_msg == '':
                        flash(gettext('Record was successfully saved.'), 'success')
                        return redirect(self.get_url('.details_view', id=model.id, url=return_url))

        if request.method == 'GET' or form.errors:
            self.on_form_prefill(form, model.id)

        return self.render('admin/flight-edit.html', form=form, model=model,
                           medium_num=medium_num, airports=dao.load_airports(),
                           sts_msg=sts_msg, medium_list=medium_list,
                           am_msg=am_msg, am_edit_msg=am_edit_msg, return_url=return_url)

    @expose('/details/')
    def details_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_view_details:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        apm_list = Flight_AirportMedium.query.filter(
            Flight_AirportMedium.flight_id.__eq__(id)
        ).all()

        return self.render("admin/flight-details.html",
                           model=model,
                           details_columns=self._details_columns,
                           get_value=self.get_detail_value,
                           apm_list=apm_list,
                           return_url=return_url)


class StatsView(AuthenticatedView):
    @expose('/')
    def index(self):
        total = Decimal(0)
        airline_name = request.args.get('airline_name')
        date = request.args.get('month')
        statistics = dao.statistic_revenue_follow_month(airline_name=airline_name,
                                                        date=date)
        for s in statistics:
            if s[2]:
                total = total + s[2]
        return self.render('admin/stats.html',
                           statistics=statistics, total=total)


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for("index"))

    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(FlightManagementView(Flight, db.session, name="Quản lý chuyến bay", endpoint='flights'))
admin.add_view(RegulationView(Regulation, db.session, name='Quy định'))
admin.add_view(StatsView(name="Thống kê báo cáo"))
admin.add_view(LogoutView(name="Đăng xuất"))
