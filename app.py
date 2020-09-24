import os
import pymongo
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
client = pymongo.MongoClient('mongodb+srv://username:account_and_password@e-vote-cluster.znrcm.mongodb.net/e-vt?retryWrites=true&w=majority')
database = client['E-vt']
collection = database['users']
e_collection = database["election"]

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.secret_key = "Aryanisgreat@/debug/e-vote/23/unhack"

@app.route("/")
def index():
    session.clear()
    return render_template("home/index.html")

@app.route("/privacypolicy")
def privacypolicy():
    """Privacy Policy for users"""
    return render_template("Policies/privacypolicy.html")

@app.route("/termsofuse")
def termsofuse():
    """Privacy Policy for users"""
    return render_template("Policies/termsofuse.html")



@app.route("/vote", methods=["GET", "POST"])
@login_required
def vote():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure name was submitted
        if not request.form.get("name"):
            return apology("must provide name", 403)

        elif not request.form.get("email"):
            return apology("must provide email", 403)

        elif not request.form.get("aadhaar"):
            return apology("must provide aadhaar card no.", 403)

        elif not request.form.get("phone"):
            return apology("must provide phone no.", 403)

        elif not request.form.get("symbol"):
            return apology("must provide party symbol", 403)                                    
 
        name = request.form.get("name")
        aadhaar = int(request.form.get("aadhaar"))
        phone = request.form.get("phone")
        symbol = request.form.get("symbol")
        email = request.form.get("email")

        user_id = session["user_id"]
        e_check = collection.find_one( { "email" : user_id } )
        database_email = e_check["email"]
        database_email = database_email.lower()
        if database_email != email.lower():
            return apology("DETAILS ARE NOT MATCHING OUR RECORD",403)
        if int(e_check["aadhaar"]) == aadhaar:
            collection.update( { "email" : user_id }, { "$set" : { "voted" : 1 } } )
            symbol = symbol.lower()
            symbol = symbol.strip()
            valid_symbol = collection.find_one( { "symbol" : symbol } )
            if valid_symbol == None:
                return apology("PLEASE ENTER VALID SYMBOL",403)
            else:
                active_election = e_collection.find_one( { "active" : 1 } )
                if valid_symbol["party"] in active_election["vote"]:
                    part_dict = active_election["vote"].copy()
                    new_vote = part_dict[valid_symbol["party"]] + 1
                    part_dict[valid_symbol["party"]] = new_vote
                    e_collection.update( { "_id" : active_election["_id"] }, { "$set" : { "vote" : part_dict } } )
                else:
                    part_dict = active_election["vote"].copy()
                    part_dict[valid_symbol["party"]] = 1
                    e_collection.update( { "_id" : active_election["_id"] }, { "$set" : { "vote" : part_dict } } )
        else:
            return apology("DETAILS ARE NOT MATCHING OUR RECORD 2",403)                                   

        return redirect("/main")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
            user_id = session["user_id"]
            vote_status = collection.find_one( { "email" : user_id } )
            if vote_status["voted"] == 0:
                state_specific = e_collection.find_one({"active" : 1})
                if state_specific is None:
                    return apology("NO RUNNING ELECTIONS",403)
                elif state_specific["s_specific"] == 1:
                    if vote_status["state"] != state_specific["state"]:
                        return apology("NO RUNNING ELECTION IN YOUR STATE",403)
                    else:
                        candidate_data = collection.find( { "type" : 1, "state" : state_specific["state"] } )
                elif state_specific["s_specific"] == 0:
                    candidate_data = collection.find( { "type" : 1 } )
                return render_template('stats/vote.html',details = candidate_data)
            else:
                return redirect("/main")                    
             
@app.route("/main")
@login_required
def main():

    user_id = session["user_id"]
    vote_status = collection.find_one( { "email" : user_id } )
    if vote_status["voted"] == 0:
        return redirect('/vote')
    election = e_collection.find_one({"active" : 1})
    max = 0
    id = 0
    winners = []
    winners.append(" ")

    # Check who has the highest vote
    if election is None:
        rows = {}
        max = 0
        totalc = collection.count_documents( { "type" : 1 } )
        voter = collection.count_documents( { "type" : 0 } )
        voted = 0
        voters = voter + totalc
        votes = {}
    else:
        rows = election["vote"]
        for key, value in election["vote"].items():
            if int(value) > max:
                party = key
                winners[0] = key

        # Checks if election tied
        for key, value in election["vote"].items():
            if value == max and key != party:
                winners.append(party)

        totalc = collection.count_documents( { "type" : 1 } )
        voter = collection.count_documents( { "type" : 0 } )
        nouser = False
        if voter == None:
            nouser = True
        vote_used = 1
        voted = collection.count_documents( { "voted" : 1 } )
        if nouser == True:
            voters = totalc
        else:
            voters = voter + totalc
        voted = (voted/voters)*100
        if election["s_specific"] == 1:
            details = collection.find({"type" : 1, "state" : election["state"]})
        else: 
            details = collection.find({"type" : 1})
        votes = election["vote"].copy()

    # Variable multi is used to inform the page whether the election is tied so that the page can be styled accordingly and winners can be printed
    if len(winners) > 1:
        multi = True
    else:
        multi = False
    details = collection.find({"type" : 1})    
    user = collection.find_one({"email" : session["user_id"]})
    if session['type'] != 2:
        return render_template(
                                    "stats/main.html",
                                    first = user["first"],
                                    last = user["last"],
                                    details = details,
                                    votes = votes,
                                    winners = winners,
                                    multi = multi,
                                    totalc = totalc,                                
                                    voters = voters,
                                    voted = "{:.2f}".format(voted)
                                )   
    elif session['type'] == 2:
        return render_template(
                                    "stats/c_dash.html",
                                    first = user["first"],
                                    last = user["last"],
                                    details = details,
                                    votes = votes,
                                    winners = winners,
                                    multi = multi,
                                    totalc = totalc,                                
                                    voters = voters,
                                    voted = "{:.2f}".format(voted)
                                )          
                               

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email id", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        email = request.form.get("email").lower()
        password = request.form.get("password")
        user = collection.find_one({"email" : email})
        # Ensure username exists and password is correct
        if user is None:
            return apology("invalid username and/or password", 403)
        if not check_password_hash(user["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user["email"]
        session["type"] = user["type"]

        # Redirect user to home page
        return redirect("/vote")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stats/login.html")

@app.route("/commission", methods=["GET", "POST"])
def commission_login():
    """Log election commission in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email id", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        email = request.form.get("email").lower()
        password = request.form.get("password")
        user = collection.find_one({"email" : email})
        # Ensure username exists and password is correct
        if user is None:
            return apology("invalid username and/or password", 403)
        if not check_password_hash(user["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        if user["type"] != 2:
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = user["email"]
        session["type"] = user["type"]

        # Redirect user to home page
        return redirect("/c_dash")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stats/commission_login.html")        

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("firstname"):
            return apology("must provide FIRST NAME", 403)

        # Ensure all fields were was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif not request.form.get("confirmation"):
            return apology("must provide password again", 403)

        elif request.form.get("password") != request.form.get("confirmation"): # Ensure passwords match
            return apology("passwords should match", 403)
        
        elif not request.form.get("email"):
            return apology("MUST PROVIDE EMAIL", 403)

        elif not request.form.get("phone"):
            return apology("MUST PROVIDE PHONE NO.", 403)

        elif not request.form.get("aadhaar"):
            return apology("MUST PROVIDE AADHAAR CARD NO.", 403)

        elif not request.form.get("country"):
            return apology("MUST PROVIDE COUNTRY NAME", 403)

        elif not request.form.get("zip"):
            return apology("MUST PROVIDE PINCODE", 403)
            
        elif not request.form.get("state"):
            return apology("MUST PROVIDE STATE NAME", 403)            
        # Query database for username
        aadhaar = int(request.form.get("aadhaar"))
        phone = int(request.form.get("phone"))
        email = request.form.get("email").lower()
        password = request.form.get("password")
        zip = request.form.get("zip")
        first = request.form.get("firstname")
        last = request.form.get("lastname")
        country = request.form.get("country")
        state = request.form.get("state").lower()
        state = state.strip()
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        x = collection.find_one({"email" : email})  #Check if email alread existes
        if x != None:
            return render_template("stats/register.html", error=1, issue="E-mail ID")

        x = collection.find_one({"phone" : phone})  #Check if phone alread existes
        if x!= None:
            return render_template("stats/register.html", error=1, issue="Phone No.")

        x = collection.find_one({"aadhaar" : aadhaar})  #Check if aadhaar alread existes
        if x != None:
            return render_template("stats/register.html", error=1, issue="Aadhaar card No.")

        x = collection.insert_one({
            "first": first,
            "last": last,
            "hash": hash,
            "aadhaar": aadhaar,
            "zip": zip,
            "phone": phone,
            "email": email,
            "voted": 0,
            "country": country,
            "state": state,
            "type": 0
        })  # Insert data of user in collection

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stats/register.html")
    return apology("INTERNAL SERVER ERROR", 404)

@app.route("/candidate-register", methods=["GET", "POST"])
def cregister():
    """Register Candidate"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("first"):
            return apology("must provide FIRST NAME", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif not request.form.get("confirmation"):
            return apology("must provide password again", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords should match", 403)
        
        elif not request.form.get("email"):
            return apology("MUST PROVIDE EMAIL", 403)

        elif not request.form.get("state"):
            return apology("MUST PROVIDE STATE NAME", 403)

        elif not request.form.get("phone"):
            return apology("MUST PROVIDE PHONE NO.", 403)

        elif not request.form.get("aadhaar"):
            return apology("MUST PROVIDE AADHAAR CARD NO.", 403)

        elif not request.form.get("country"):
            return apology("MUST PROVIDE COUNTRY NAME", 403)

        elif not request.form.get("zip"):
            return apology("MUST PROVIDE PINCODE", 403)
        
        elif not request.form.get("pname"):
            return apology("MUST PROVIDE PARTY NAME", 403)
        
        elif not request.form.get("symbol"):
            return apology("MUST PROVIDE Party Symbol", 403)

        if not request.form.get("last"):
            last = ""
        else:
            last = request.form.get("last")
        # Query database for username
        aadhaar=request.form.get("aadhaar") 
        phone=request.form.get("phone")   
        email = request.form.get("email").lower()
        password = request.form.get("password")
        zip = request.form.get("zip")
        first = request.form.get("first")
        symbol = request.form.get("symbol").lower()
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        party = request.form.get("pname")
        country = request.form.get("country")
        state = request.form.get("state").lower()
        state = state.strip()

        x = collection.find_one({"email" : email})  #Check if email alread existes
        if x != None:
            return render_template("stats/candidate-register.html", error=1, issue="E-mail ID")

        x = collection.find_one({"phone" : phone})  #Check if phone alread existes
        if x != None:
            return render_template("stats/candidate-register.html", error=1, issue="Phone No.")

        x = collection.find_one({"email" : aadhaar})  #Check if aadhaar alread existes
        if x != None:
            return render_template("stats/candidate-register.html", error=1, issue="Aadhaar card No.")

        x = collection.insert_one({
            "first": first,
            "last": last,
            "hash": hash,
            "aadhaar": aadhaar,
            "zip": zip,
            "state": state,
            "phone": phone,
            "email": email,
            "voted": 0,
            "country": country,
            "type": 1,
            "party": party,
            "symbol": symbol.lower() # Using lowercase symbol to make voting easier without extra variables
        })  # Insert data of user in collection
        
        # Redirect user to home page
        return redirect("/candidate-login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stats/cregister.html")

    return apology("INTERNAL SERVER ERROR", 404) #IF something breaks

@app.route("/hold", methods=["GET", "POST"])
@login_required
def hold():
    if request.method == "POST":

        if session["type"] is not 2:
            return redirect("/main")

        # Ensure name was submitted
        if not request.form.get("elect_name"):
            return apology("must provide election name", 403)

        elif not request.form.get("email"):
            return apology("must provide email", 403)

        elif not request.form.get("country"):
            return apology("must provide country name", 403)

        elif not request.form.get("Start_date"):
            return apology("must provide election start date", 403)

        elif not request.form.get("Start_time"):
            return apology("must provide election start time", 403)                                    

        elif not request.form.get("End_date"):
            return apology("must provide election start date", 403)

        elif not request.form.get("End_time"):
            return apology("must provide election start time", 403) 

        if not request.form.get("state_required"):
            s_specific = 0
            state = ""
        elif int(request.form.get("state_required")) == 1:
            if not request.form.get("state"):
                return apology("must provide state name", 403)
            else:
                s_specific = 1
                state = request.form.get("state").lower()
                state = state.strip()

        if s_specific == 1:
            collection.update( { "state" : state, "type" : 1 }, { "$set" : { "voted" : 0 } } )
            collection.update( { "state" : state, "type" : 0 }, { "$set" : { "voted" : 0 } } )
        else:
            collection.update( { "type" : 1 }, { "$set" : { "voted" : 0 } } )
            collection.update( { "type" : 0 }, { "$set" : { "voted" : 0 } } )
        elect_name = request.form.get("elect_name")
        country = request.form.get("country")
        email = request.form.get("email")

        user_id = session["user_id"]
        e_check = collection.find_one( { "email" : user_id } )
        database_email = e_check["email"]
        database_email = database_email.lower()
        if database_email != email.lower():
            return apology("DETAILS ARE NOT MATCHING OUR RECORD",403)
        x = e_collection.insert_one({
            "e_name": elect_name,
            "email": session["user_id"],
            "state": state,
            "country": country,
            "s_specific": s_specific,
            "start_date": request.form.get("Start_date"),
            "start_time": request.form.get("Start_time"),
            "end_date": request.form.get("End_date"),
            "end_time": request.form.get("End_time"),
            "active": 1,
            "vote": {}
        })

        return redirect("/main")        

    else:
        x = e_collection.find_one({"active" : 1})  #Check if an election already exists
        if x != None:
            return redirect("/main")
        if session["type"] is 2:
            return render_template("stats/new_elect.html")
        else:
            return redirect("/main")

# @app.route("/val", methods=["GET", "POST"])
# def val():
#     if request.method =="POST":
#         sd = request.form.get("Start_date")
#         et = request.form.get("End_time")
#         return render_template("stats/t1.html", sd = sd, et = et)
#     else:
#         return render_template("stats/val.html")

@app.route("/elections")
@login_required
def current():
    if session["type"] is 2:
        elections = e_collection.find( { "active" : 1 } )
        candidate_data = collection.find( { "type" : 1 } )
        return render_template('stats/current_elect.html',d1 = elections, details = candidate_data)
    else:
        return redirect("/main")



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        return redirect("/change")
    else:
        username = collection.find_one({"email" : session["user_id"]})
        return render_template("stats/profile.html", first = username["first"], last = username["last"])

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure Old password was submitted
        if not request.form.get("oldpass"):
            return apology("must provide OLD PASSWORD", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide new password", 403)

        elif not request.form.get("confirmation"):
            return apology("must provide password again", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords should match", 403)

        old_pass = collection.find_one({"email" : session["user_id"]})
        if not check_password_hash(old_pass["hash"], request.form.get("oldpass")):
            return apology("invalid password", 403)
        else:
            password = request.form.get("password")
            hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            collection.update( { "email" : session["user_id"] }, { "$set" : { "hash" : hash } } )
            return render_template("stats/password_change.html", success = 1)

    else:
        return render_template("stats/password_change.html")

    return apology("INTERNAL SERVER ERROR", 404)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
	
if __name__ == '__main__':
    app.run()
