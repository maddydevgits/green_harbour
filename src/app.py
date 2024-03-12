from web3 import Web3,HTTPProvider
import json
from shutil import RegistryError
from flask import Flask,render_template,request,session,redirect
from pymongo import MongoClient
from bson import ObjectId
import urllib3
from datetime import datetime



blockchain="http://127.0.0.1:7545"
web3=Web3(HTTPProvider(blockchain))
app=Flask(__name__)
app.secret_key = '30c0'

dbClient=MongoClient('mongodb://localhost:27017/')
db=dbClient['green_harbor']
user_details1=db['user_details']
bin_details=db['bin_detail']
token_details=db['token_details1']
filled_bins=db['filled_bins']
notifications=db['notifications']

def pushnotifications(notification,notfrom,notto,nottime):
    k={}
    k['notification']=notification
    k['from']=notfrom
    k['to']=notto
    k['timestamp']=nottime
    notifications.insert_one(k)

def connectWithBlockchain():
    web3.eth.defaultAccount=web3.eth.accounts[0]
    
    artifact="./build/contracts/TokenManagementSystem.json"
    with open(artifact,'r') as f:
        artifact_json=json.loads(f.read())
        contract_abi=artifact_json['abi'] 
        contract_address=artifact_json['networks']['5777']['address'] 
    
    contract=web3.eth.contract(
        abi=contract_abi,
        address=contract_address
    )
    return contract,web3

def readDataFromThingSpeak(channelid):
    http=urllib3.PoolManager()
    response=http.request('get','https://api.thingspeak.com/channels/'+str(channelid)+'/feeds.json')
    response=response.data
    response=response.decode('utf-8')
    
    response=json.loads(response)
    pushnotifications('Reading Data from IoT','Blockchain',session['b'],datetime.now())
    return response['feeds']

@app.route('/')
def openPage():
    return render_template('open.html')

@app.route('/register')
def signupPage():
    return render_template('register.html')

@app.route('/login')
def loginPage():
    return render_template('login.html')

@app.route('/open')
def logoutPage():
    return render_template('open.html')

@app.route('/about')
def aboutPage():
    return render_template('about.html')

@app.route('/adminlogin')
def AloginPage():
    return render_template('adminlogin.html')

@app.route('/dlogin')
def dloginPage():
    return render_template('driverlogin.html')

@app.route('/dashboard')
def DashPage():
    return render_template('dashboard.html')

@app.route('/qrcode')
def QRPage():
    return render_template('qrcode.html')

@app.route('/admindashboard')
def Adashboard():
    return render_template('admindashboard.html')

@app.route('/bindata')
def bindata1():
    return render_template('bindata.html')

@app.route('/profile',methods=['POST','GET'])
def profile():
    profile_details=user_details1.find_one({"phno":session['b']})
    
    if profile_details:
        Name=profile_details.get('Name')
        Sector=profile_details.get('Sector')
        Org_name=profile_details.get('Org_name')
        email=profile_details.get('email')
        phno=profile_details.get('phno')
        address=profile_details.get('address')
        contract,web3=connectWithBlockchain()
        _phoneno,_tokens=contract.functions.viewTokens().call()
        phoneindex=_phoneno.index(int(session['b']))
        no_of_tokens=_tokens[phoneindex]
        latitude=profile_details.get('lat')
        longitude=profile_details.get('lon')
        channelid=profile_details.get('channelid')
        
    return render_template("profile.html",Name=Name,Sector=Sector,Org_name=Org_name,email=email,phno=phno,address=address,no_of_tokens=no_of_tokens,latitude=latitude,longitude=longitude,channelid=channelid)

@app.route('/bindata.html',methods=['POST','GET'])
def bindata():
    user=user_details1.find({'phno':session['b']})
    data=[]
    if user:
        for i in user:
            channelid=i.get('channelid')
            print(channelid)
            if channelid==None:
                return render_template('bindata.html',data=data)
            else:
                k=readDataFromThingSpeak(channelid)
                print(k)
                for i in k:
                    if(float(i['field2'])>0):
                        dummy=[]
                        dummy.append(i['created_at'])
                        dummy.append(i['entry_id'])
                        dummy.append(i['field1'])
                        dummy.append(i['field2'])
                        data.append(dummy)

    # bin_details1=bin_details.find({'phno':b})
    # data=[]
    # if bin_details1:
    #     for i in bin_details1:
    #         dummy=[]
    #         dummy.append(i.get('_id'))
    #         dummy.append(i.get('bin_weight'))
    #         dummy.append(i.get('bin_level'))
    #         data.append(dummy)
    
    return render_template('bindata.html',data=data)

@app.route('/userDetails',methods=['POST','GET'])
def users():
    details1=user_details1.find()
    data1=list(details1)
    print(data1)
    data=[]
    if len(data1)>0:
        for i in data1:
            dummy=[]
            dummy.append(i.get('_id'))
            dummy.append(i.get('Name'))
            dummy.append(i.get('Sector'))
            dummy.append(i.get('Org_name'))
            dummy.append(i.get('email'))
            dummy.append(i.get('phno'))
            dummy.append(i.get('address'))
            try:
                dummy.append(i.get('lat'))
            except:
                dummy.append(0)
            print(dummy)
            data.append(dummy)
    else:
        # print('no data')       
        # print(data)
        data="no data found"
    return render_template('user_details.html',data=data)

@app.route('/binDetails',methods=['POST','GET'])
def bins():
    # The line `details=bin_details.find({'bin_level':{:80}})` is attempting to find documents in
    # the `bin_details` collection where the value of the field `bin_level` is greater than 80.

    contract,web3=connectWithBlockchain()
    _entryids,_binweight,_itokens,_iphoneno=contract.functions.viewTransactions().call()

    data=[]
    for i in range(len(_entryids)):
        dummy=[]
        dummy.append(_binweight[i])
        dummy.append(_itokens[i])
        dummy.append(_iphoneno[i])
        for j in user_details1.find({'phno':str(_iphoneno[i])}):
            print(j)
            dummy.append(j['lat'])
            dummy.append(j['lon'])
            dummy.append(j['channelid'])
        data.append(dummy)
    
    if len(_entryids)==0:
        # print('no data')       
        # print(data)
        data="no data found"
    return render_template('bin_details.html',data=data)


@app.route('/collectData',methods=['POST'])
def collectData():
    Name=request.form['Name']
    Sector=request.form['Sector']
    Org_name=request.form['Org_name']
    email=request.form['email']
    pwd=request.form['pwd']
    phno=request.form['phno']
    address=request.form['address']
    
    existing_user=user_details1.find_one({'phno':phno})
    if existing_user:
        msg="existing user"
        return render_template('register.html',msg=msg)
    
    user_data={
        'Name':Name,
        'Sector':Sector,
        'Org_name':Org_name,
        'email':email,
        'pwd':pwd,
        'phno':phno,
        'address':address
    }
    user_details1.insert_one(user_data)
    try:
        contract,web3=connectWithBlockchain()
        tx_hash=contract.functions.addToken(int(phno),0).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)
    except:
                pass
    
    return render_template('login.html')


@app.route('/Details',methods=['POST'])
def data():
    phno=request.form['phno']
    pwd=request.form['pwd']
    user=user_details1.find_one({'phno':phno})
    if user:
        global b
        b=user.get('phno')
        
        if user.get('pwd')==pwd:
            session['b']=phno
            msg='login successful'
            try:
                contract,web3=connectWithBlockchain()
                tx_hash=contract.functions.addToken(int(phno),0).transact()
                web3.eth.waitForTransactionReceipt(tx_hash)
            except:
                pass
            return render_template('dashboard.html',msg=msg)
        else:
            msg='password wrong'
            return render_template('login.html',msg=msg)
    else:
        msg='user not found'
        return render_template('login.html',msg=msg)
    
@app.route('/dlogin', methods=['POST','GET'])
def dlog():
    Username=request.form['Username']
    pwd=request.form['pwd']
    flag=0
    if(Username=='driver' and pwd=='trucks'):
        flag=1
        session['Username']=Username
        session['pwd']=pwd
        return render_template('driverdashboard.html')
    if flag==0:
        msg='INVALID USERNAME OR PASSWORD'
        return render_template('driverlogin.html',msg=msg)

@app.route('/driverdashboard')
def driverdashboard():
    return render_template('driverdashboard.html')

@app.route('/routeDetails')
def routeDetails():
    data=user_details1.find()
    data1=[]
    for i in data:
        try:
            binid=i['channelid']
            binlat=i['lat']
            binlon=i['lon']
            dummy=[binid,binlat,binlon]
            data1.append(dummy)
        except:
            continue
    return render_template('routeDetails.html',data=data1)
 
@app.route('/Alogin',methods=['POST'])
def Adata():
    Username=request.form['Username']
    pwd=request.form['pwd']
    flag=0
    if(Username=='admin' and pwd=='admin123'):
        flag=1
        session['Username']=Username
        session['pwd']=pwd
        return render_template('admindashboard.html')
    if flag==0:
        msg='INVALID USERNAME OR PASSWORD'
        return render_template('adminlogin.html',msg=msg)

    
@app.route('/userTokens',methods=['POST','GET'])
def usertokens():
    user_data=user_details1.find_one({'phno':session['b']})
    # print(user_data)
    if user_data!=None:
        try:
            channelid=user_data['channelid']
        except:
            channelid=None
    # print(channelid)
    sum=0
    if channelid!=None:
        k=readDataFromThingSpeak(channelid)
        print(k)
        for i in k:
                contract,web3=connectWithBlockchain()
                _entryids,_binweight,_itokens,_iphoneno=contract.functions.viewTransactions().call()
                if int(i['entry_id']) in _entryids:
                    continue
                bin_weight=float(i['field2'])
                if bin_weight<=0:
                    continue
                itoken=bin_weight/2
                tx_hash=contract.functions.addTransaction(int(i['entry_id']),int(bin_weight),int(itoken),int(session['b'])).transact()
                
                web3.eth.waitForTransactionReceipt(tx_hash)
    
    contract,web3=connectWithBlockchain()
    _entryids,_binweight,_itokens,_iphoneno=contract.functions.viewTransactions().call()
    data=[]

    for i in range(len(_entryids)):
        if(_iphoneno[i]==int(session['b'])):
            dummy=[]
            dummy.append(_entryids[i])
            dummy.append(_binweight[i])
            dummy.append(_itokens[i])
            dummy.append(_itokens[i]*6.5)
            data.append(dummy)
    
    contract,web3=connectWithBlockchain()
    _phoneno,_tokens=contract.functions.viewTokens().call()

    phoneindex=_phoneno.index(int(session['b']))
    sum=_tokens[phoneindex]

    pushnotifications('Tokens Updated','Blockchain',session['b'],datetime.now())

    return render_template('user_tokens.html',data=data,sum=sum)

@app.route('/notifications.html')
def notificationsPage():
    data=notifications.find()
    data1=[]
    for i in data:
        if i['to']==session['b']:
            dummy=[]
            dummy.append(i['_id'])
            dummy.append(i['notification'])
            dummy.append(i['from'])
            dummy.append(i['timestamp'])
            data1.append(dummy)
    print(data1)
    return render_template('notifications.html',data=data1)

@app.route('/allocatebin/<id>')
def allocatebin(id):
    print(id)
    session['_id']=id
    return render_template('abin.html')

@app.route('/configurebin',methods=['POST'])
def configurebin():
    lat=request.form['lat']
    lon=request.form['lon']
    channelid=request.form['channelid']
    print(lat,lon,channelid)
    user_details1.update({'_id':ObjectId(session['_id'])},{'$set':{'lat':lat,'lon':lon,'channelid':channelid}})
    return render_template('abin.html',msg='bin added successfully')

@app.route('/transferTokens')
def transferTokens():
    contract,web3=connectWithBlockchain()
    _phoneno,_tokens=contract.functions.viewTokens().call()
    print(_phoneno,_tokens)
    tokens=None
    for i in range(len(_phoneno)):
        if str(_phoneno[i])==session['b']:
            tokens=_tokens[i]
            session['mytokens']=tokens
    return render_template('transfertokens.html',tokens=tokens)

@app.route('/transfertokensdata',methods=['post'])
def transfertokensdata():
    ph=request.form['ph']
    tok=request.form['tok']
    if(int(tok)<session['mytokens']):
        contract,web3=connectWithBlockchain()
        tx_hash=contract.functions.transferToken(int(session['b']),int(ph),int(tok)).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)
        contract,web3=connectWithBlockchain()
        _phoneno,_tokens=contract.functions.viewTokens().call()
        tokens=None
        for i in range(len(_phoneno)):
            if str(_phoneno[i])==session['b']:
                tokens=_tokens[i]
                session['mytokens']=tokens
        
        pushnotifications(str(tok)+' Tokens Transfered to '+str(ph),'Blockchain',session['b'],datetime.now())
        pushnotifications(str(tok)+' Tokens Received from '+str(session['b']),'Blockchain',ph,datetime.now())

        return render_template('transfertokens.html',tokens=tokens,msg='Transfered')
    else:
        contract,web3=connectWithBlockchain()
        _phoneno,_tokens=contract.functions.viewTokens().call()
        tokens=None
        for i in range(len(_phoneno)):
            if str(_phoneno[i])==session['b']:
                tokens=_tokens[i]
                session['mytokens']=tokens
        return render_template('transfertokens.html',tokens=tokens,msg='Insufficient Funds')

if __name__=="__main__":
    app.run(port=9001,debug=True)