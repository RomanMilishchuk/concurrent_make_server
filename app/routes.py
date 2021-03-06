from flask import jsonify, request, Blueprint
from models import Node, User, Compiler, Os, Computer
from __init__ import app, db

nodes = Blueprint('/nodes', __name__)

def view_helper():
    summary = db.engine.execute("select * from node_summary")
    objs = []
    for i in summary:
        obj = {}
        obj['id'] = i[0]
        obj['user_name'] = i[1]
        obj['compiler_name'] = i[2]
        obj['major_version'] = i[3]
        obj['minor_version'] = i[4]
        obj['os_name'] = i[5]
        objs.append(obj)
    return objs

def get_computer(form):
    cur_compiler = Compiler.query.filter_by(compiler_name=form["compiler_name"]).filter_by(major_version=int(form["major_version"])).filter_by(minor_version=int(form["minor_version"])).first()

    if cur_compiler is None:
        cur_compiler = Compiler(compiler_name=form["compiler_name"], major_version=int(form["major_version"]), minor_version=int(form["minor_version"]))
    cur_os = Os.query.filter_by(os_name=form["os_name"]).first()
    if cur_os is None:
        cur_os = Os(os_name=form["os_name"])
    cur_computer = Computer.query.filter_by(compiler_id = cur_compiler.compiler_id, os_id=cur_os.os_id).first()
    if cur_computer is None:
        cur_computer = Computer(compiler_name = cur_compiler, os_name=cur_os)
    return cur_computer


@app.route("/node_summary", methods=["GET"])
def get_summary():
    objs = view_helper()
    return jsonify(objs), 200


@nodes.route("/", methods=["POST"])
def create_node():
    form = request.get_json()
    print(form)
    public_key = form["public_key"]
    ip = form["ip"]
    login = form["login"]
    user = User.query.filter_by(user_name=login).first()
    if not user:
        user = User(user_name=login)
    user_list = Node.query.filter_by(public_key=public_key).all()
    if not len(user_list):
        node = Node(public_key=public_key, ip=ip, login=user)
    else:
        return "Data is already posted", 409

    node.node_computer = get_computer(form)
    db.session.add(node)
    db.session.commit()
    return "Posted", 200


@nodes.route("/", methods=["PUT"])
def change_node():
    new_node = request.get_json()
    node = Node.query.filter_by(public_key=new_node["public_key"]).first()
    if (node is None):
        return "Node is not found", 404
    node.ip = new_node["ip"]
    cur_user = User.query.filter_by(user_name=new_node["login"]).first()
    if cur_user is None:
        cur_user = User(user_name=new_node["login"])
    node.login = cur_user

    node.node_computer = get_computer(new_node)
    db.session.commit()
    return jsonify(eval(str(new_node))), 200


@app.route("/get_ips", methods=["GET"])
def get_ips():
    req_dict = request.args.to_dict()
    try:
        req_dict["minor_version"] = int(req_dict["minor_version"])
    except:
        pass
    try:
        req_dict["major_version"] = int(req_dict["major_version"])
    except:
        pass
    objects = view_helper()
    filtered_objs = list(filter(lambda x: all(item in x.items() for item in req_dict.items()), objects))
    addresses = []
    for node in filtered_objs:
        cur = Node.query.get(node["id"])
        addresses.append({"address": node["user_name"] + "@" + cur.ip})
    return jsonify({"addresses": addresses})


@app.route("/get_public_keys", methods=["GET"])
def get_pk():
    pks = []
    for node in Node.query.all():
        pks.append({"public_key": node.public_key})
    return jsonify({"public_keys": pks})


@app.route("/<int:id_u>", methods=["DELETE"])
def delete(id_u):
    if (id_u,) not in db.session.query(Node.id).all():
        return "There is no such student in database", 404

    db.session.query(Node).filter(Node.id == id_u).delete(
        synchronize_session='evaluate')
    db.session.commit()
    return "Everything fine", 200