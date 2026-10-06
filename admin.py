import os

from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for

from config import ADMIN_PASSWORD, ADMIN_PORT, ADMIN_USERNAME, SECRET_KEY
from database import Order, Product, SessionLocal, init_db

app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return redirect(url_for("orders"))


@app.route("/products")
@login_required
def products():
    with SessionLocal() as s:
        items = s.query(Product).order_by(Product.id).all()
        data = [(p.id, p.name, float(p.price), p.is_active) for p in items]
    return render_template("products.html", products=data)


@app.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    if request.method == "POST":
        with SessionLocal() as s:
            s.add(Product(
                name=request.form["name"],
                description=request.form.get("description", ""),
                price=request.form["price"],
                is_active=bool(request.form.get("is_active")),
            ))
            s.commit()
        return redirect(url_for("products"))
    return render_template("product_form.html", product=None)


@app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def product_edit(pid):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if not p:
            return "Not found", 404
        if request.method == "POST":
            p.name = request.form["name"]
            p.description = request.form.get("description", "")
            p.price = request.form["price"]
            p.is_active = bool(request.form.get("is_active"))
            s.commit()
            return redirect(url_for("products"))
        data = {"id": p.id, "name": p.name, "description": p.description, "price": float(p.price), "is_active": p.is_active}
    return render_template("product_form.html", product=data)


@app.route("/products/<int:pid>/delete", methods=["POST"])
@login_required
def product_delete(pid):
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if p:
            s.delete(p)
            s.commit()
    return redirect(url_for("products"))


@app.route("/orders")
@login_required
def orders():
    with SessionLocal() as s:
        items = s.query(Order).order_by(Order.id.desc()).limit(200).all()
        data = [
            (o.id, o.full_name, o.phone, o.status, float(o.total), o.created_at.strftime("%d.%m.%Y %H:%M"))
            for o in items
        ]
    return render_template("orders.html", orders=data, statuses=Order.STATUSES)


@app.route("/orders/<int:oid>")
@login_required
def order_detail(oid):
    with SessionLocal() as s:
        o = s.get(Order, oid)
        if not o:
            return "Not found", 404
        items = [(i.product_name, i.quantity, float(i.unit_price)) for i in o.items]
        data = {
            "id": o.id, "full_name": o.full_name, "phone": o.phone, "address": o.address,
            "comment": o.comment, "status": o.status, "total": float(o.total),
            "username": o.username, "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
        }
    return render_template("order_detail.html", order=data, items=items, statuses=Order.STATUSES)


@app.route("/orders/<int:oid>/status", methods=["POST"])
@login_required
def order_status(oid):
    status = request.form.get("status")
    with SessionLocal() as s:
        o = s.get(Order, oid)
        if o and status in Order.STATUSES:
            o.status = status
            s.commit()
    return redirect(url_for("order_detail", oid=oid))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", ADMIN_PORT))
    app.run(host="0.0.0.0", port=port, debug=False)
