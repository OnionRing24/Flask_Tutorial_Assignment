from flask import Flask, render_template, request, redirect
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/boatdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


# render a file
@app.route('/')
def index():
    return render_template('index.html')


# remember how to take user inputs?
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# get all boats
# this is done to handle requests for two routes -
@app.route('/boats/')
@app.route('/boats/<page>')
def get_boats(page=1):
    page = int(page)
    per_page = 10
    
    # Validate sort_by parameter (whitelist approach)
    allowed_sort_fields = ['id', 'name', 'rental_price']
    sort_by = request.args.get('sort_by', 'id')
    if sort_by not in allowed_sort_fields:
        sort_by = 'id'
    
    # Validate sort_order parameter
    sort_order = request.args.get('sort_order', 'ASC').upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'ASC'
    
    # Build WHERE clause dynamically from query parameters (if present)
    conditions = []
    params = {}
    
    if request.args.get('id'):
        conditions.append("id = :id")
        params['id'] = request.args['id']
    
    if request.args.get('name'):
        conditions.append("name LIKE :name")
        params['name'] = f"%{request.args['name']}%"
    
    if request.args.get('type'):
        conditions.append("type LIKE :type")
        params['type'] = f"%{request.args['type']}%"
    
    if request.args.get('owner_id'):
        conditions.append("owner_id = :owner_id")
        params['owner_id'] = request.args['owner_id']
    
    if request.args.get('rental_price'):
        conditions.append("rental_price = :rental_price")
        params['rental_price'] = request.args['rental_price']
    
    # Build the query
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    order_by_clause = f"ORDER BY {sort_by} {sort_order}"
    
    # Get paginated results
    query = f"SELECT * FROM boats WHERE {where_clause} {order_by_clause} LIMIT {per_page} OFFSET {(page - 1) * per_page}"
    boats = conn.execute(text(query), params).all()
    
    # Preserve search params for pagination links
    search_params = {
        'id': request.args.get('id', ''),
        'name': request.args.get('name', ''),
        'type': request.args.get('type', ''),
        'owner_id': request.args.get('owner_id', ''),
        'rental_price': request.args.get('rental_price', '')
    }
    
    print(boats)
    return render_template('boats.html', boats=boats, page=page, per_page=per_page, search_params=search_params, sort_by=sort_by, sort_order=sort_order)


@app.route('/search', methods=['GET'])
def search_get_request():
    return render_template('boats_search.html')


@app.route('/search', methods=['POST'])
def search_boat():
    try:
        # Build query string from form data
        query_string = "?"
        params_list = []
        
        if request.form.get('id'):
            params_list.append(f"id={request.form['id']}")
        if request.form.get('name'):
            params_list.append(f"name={request.form['name']}")
        if request.form.get('type'):
            params_list.append(f"type={request.form['type']}")
        if request.form.get('owner_id'):
            params_list.append(f"owner_id={request.form['owner_id']}")
        if request.form.get('rental_price'):
            params_list.append(f"rental_price={request.form['rental_price']}")
        
        query_string += "&".join(params_list)
        
        # Redirect to /boats with search parameters
        return redirect(f"/boats/{query_string}")
    
    except Exception as e:
        error = str(e)
        return render_template('boats_search.html', error=error, success=None)


@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


@app.route('/create', methods=['POST'])
def create_boat():
    # you can access the values with request.from.name
    # this name is the value of the name attribute in HTML form's input element
    # ex: print(request.form['id'])
    try:
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"),
            request.form
        )
        return render_template('boats_create.html', error=None, success="Data inserted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)


@app.route('/delete', methods=['GET'])
def delete_get_request():
    return render_template('boats_delete.html')


@app.route('/delete', methods=['POST'])
def delete_boat():
    try:
        result = conn.execute(
            text("DELETE FROM boats WHERE id = :id"),
            request.form
        )
        
        if result.rowcount == 0:
            return render_template('boats_delete.html', error="Boat not found!", success=None)
        
        return render_template('boats_delete.html', error=None, success="Data deleted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_delete.html', error=error, success=None)


@app.route('/update/<int:boat_id>', methods=['GET'])
def update_get_request(boat_id):
    try:
        # Fetch the boat data to pre-fill the form
        boat = conn.execute(
            text("SELECT * FROM boats WHERE id = :id"),
            {'id': boat_id}
        ).fetchone()
        
        if boat is None:
            return render_template('boats_update.html', error="Boat not found!", boat=None)
        
        return render_template('boats_update.html', boat=boat)
    except Exception as e:
        error = str(e)
        return render_template('boats_update.html', error=error, boat=None)


@app.route('/update/<int:boat_id>', methods=['POST'])
def update_boat(boat_id):
    try:
        conn.execute(
            text("UPDATE boats SET name = :name, type = :type, owner_id = :owner_id, rental_price = :rental_price WHERE id = :id"),
            {
                'id': boat_id,
                'name': request.form['name'],
                'type': request.form['type'],
                'owner_id': request.form['owner_id'],
                'rental_price': request.form['rental_price']
            }
        )
        return render_template('boats_update.html', error=None, success="Data updated successfully!", boat=request.form)
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_update.html', error=error, success=None, boat=request.form)


if __name__ == '__main__':
    app.run(debug=True)
