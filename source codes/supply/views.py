from django.shortcuts import render
import json
from web3 import Web3
from .models import LoadStorage, ImageModel
import base64
import time
from django.http import JsonResponse


##Block chain data
##Contract for Userdata
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
contract_address = "0x3011B21ab306b4D7305A0655357718F53E9316f4"
app_user = "0x675b1984AdD80fa6A96747daD5370262D31f2A77"
web3.eth.defaultAccount = web3.eth.accounts[0]
with open("Blocks/build/contracts/UsersInfo.json") as abiFile:
    abidata = json.load(abiFile)
    abi = abidata["abi"]
    contract = web3.eth.contract(address=contract_address, abi=abi)
##Contract for Product
contract_address_product = "0x0CD3EB86654D8847891ED309FA3364Fd2e676B4a"
with open("Blocks/build/contracts/ProductInfo.json") as abiFileRepo:
    abidataPoint = json.load(abiFileRepo)
    abiPoint = abidataPoint["abi"]
    contract_product = web3.eth.contract(address=contract_address_product, abi=abiPoint)

##Contract for purchase
contract_adresss_purchase = "0x6ED668069C5C9eCB874AA81145F052AbaA7169Db"
with open("Blocks/build/contracts/PurchaseHistory.json") as purchase:
    abidataFile = json.load(purchase)
    abiPosition = abidataFile["abi"]
    contract_purchase = web3.eth.contract(
        address=contract_adresss_purchase, abi=abiPosition
    )

userDetails = {}


##Block chain
def index(request, data={}):
    store = LoadStorage.objects.all()
    if store.exists():
        result = store.first()
        data = {"mobile": result.mobile, "email": result.email}
        userDetails = data
        if result.mobile == "0123456789" and result.email == "admin@gmail.com":
            return render(request, "adminHome.html", data)
        else:
            id, image, name, qty, cost = contract_product.functions.getProducts(
                app_user
            ).call()
            data = []
            if len(id) == 0:
                data = {"message": "No Items"}
                return render(request, "userMain.html", data)
            for i in range(len(name)):
                imageFrom = ImageModel.objects.get(time=image[i])
                data.append(
                    {
                        "imageId": image[i],
                        "image": f"data:image/png;base64,{imageFrom.image_base64}",
                        "name": name[i],
                        "qty": qty[i],
                        "cost": cost[i],
                    }
                )
            return render(request, "userMain.html", context={"products": data})
    else:
        return render(request, "index.html", data)

def searchOptions(request):
    if request.method=="GET":
        search=request.GET.get("search","")
        id, image, name, qty, cost = contract_product.functions.getProducts(
                app_user
            ).call()
        data = []
        if len(id) == 0:
                data = {"message": "No Items"}
                return render(request, "userMain.html", data)
        for i in range(len(name)):
            if search in name[i]: 
                imageFrom = ImageModel.objects.get(time=image[i])
                data.append(
                    {
                        "imageId": image[i],
                        "image": f"data:image/png;base64,{imageFrom.image_base64}",
                        "name": name[i],
                        "qty": qty[i],
                        "cost": cost[i],
                    }
                )

        return  JsonResponse(
                {"status": "success", "message": search,"data":data}
            )

def signup(request, data={}):
    return render(request, "signup.html", data)


def signupSubmit(request):
    if request.method == "GET":
        print("i am Callinf")
        email = request.GET.get("email", "")
        password = request.GET.get("password", "")
        mobile = request.GET.get("mobile", "")
        name = request.GET.get("name", "")
        address = request.GET.get("address", "")
        email1 = contract.functions.getEveryUser(app_user).call({
            'from':app_user
        })
        print(email1)
        if email.lower() in email1[2]:
            return JsonResponse(
                {"status": "success", "message": "Try with another email"}
            )
        else:
            contract.functions.addUser(password, name, address, mobile, email).transact(
                {
                    "from": app_user,
                    "nonce": web3.eth.get_transaction_count(app_user),
                    "gas": 600000,
                }
            )
            return JsonResponse({"status": "success", "message": "Success"})


def testPage(request):
    # LoadStorage.objects.all().delete()
    # ImageModel.objects.all().delete()
    id, name, email, mobile, address = contract.functions.getEveryUser(app_user).call()
    users = []
    nothing = [name, email, mobile, address, id]
    print(nothing)
    for i in range(len(email)):
        users.append({"email": email[i], "mobile": mobile[i]})
    products = []
    id, name, image, qty, cost = contract_product.functions.getProducts(app_user).call()
    order = contract_purchase.functions.getDataHistory().call({"from": app_user})
    print(order)
    for i in range(len(name)):
        products.append(
            {"image": image[i], "name": name[i], "qty": qty[i], "cost": cost[i]}
        )
    return render(request, "test.html", context={"users": users})


def loginSubmit(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        id, name, address, email1, mobile = contract.functions.loginSubmit(
            app_user, email, password
        ).call()
        data = {"email": email, "password": password}
        if email == "admin@gmail.com" and password == "admin":
            data = ""
            LoadStorage(0, "admin@gmail.com", "0123456789").save()
            return render(request, "adminHome.html")
        elif email1 == "" and mobile == "":
            data["message"] = "Invalid user"
        else:
            print([id, name, address, email1, mobile])
            storageCredentials(request, email1, mobile, address, name, id, password)
        return index(request, data)


def storageCredentials(request, email, mobile, address, name, id, password):
    LoadStorage(0, email, mobile, password, address, name, id).save()
    return render(request, "userMain.html")


def addProduct(request):
    data = {}
    if request.method == "POST":
        filePath = request.FILES.get("image", None)
        pname = request.POST.get("pname", None)
        pqty = request.POST.get("pqty", None)
        cost = request.POST.get("cost", None)

        string = "Please enter the Product"
        if not filePath:
            data["message"] = "Choose iamge from your Gallery"
        elif not pname:
            data["nameError"] = f"{string} Name"
        elif not pqty:
            data["QtyError"] = f"{string} Qty"
        elif not cost:
            data["CostError"] = f"{string} Cost"
        else:
            encoded = encodeImage(filePath)
            timeInMill = round(time.time() * 1000)
            ImageModel.objects.create(image_base64=encoded, time=timeInMill)
            contract_product.functions.addProduct(
                str(timeInMill), pname, int(pqty), int(cost)
            ).transact(
                {
                    "from": app_user,
                    "nonce": web3.eth.get_transaction_count(app_user),
                    "gas": 600000,
                }
            )
            data = {"message": "Successfully Added"}

        return render(request, "adminHome.html", context=data)


def encodeImage(image):
    return base64.b64encode(image.read()).decode("utf-8")


def viewItems(request):
    id, image, name, qty, cost = contract_product.functions.getProducts(app_user).call()
    data = []
    for i in range(len(name)):
        imageFrom = ImageModel.objects.get(time=image[i])
        data.append(
            {
                "id": id[i],
                "image": f"data:image/png;base64,{imageFrom.image_base64}",
                "name": name[i],
                "qty": qty[i],
                "cost": cost[i],
            }
        )

    return render(request, "adminViewItems.html", context={"products": data})


def adminCart(request):
    data = []
    id, name, mobile, email, addresses, pname, image, status, qty, cost, total = (
        contract_purchase.functions.getDataHistory().call({"from": app_user})
    )
    for i in range(len(id)):
        photo = ImageModel.objects.get(time=image[i])
        data.append(
            {
                "id": id[i],
                "name": name[i],
                "mobile": mobile[i],
                "email": email[i],
                "addresses": addresses[i],
                "pname": pname[i],
                "image": f"data:image/png;base64,{photo.image_base64}",
                "status": status[i],
                "qty": qty[i],
                "cost": cost[i],
                "total": total[i],
                "imageId": image[i],
            }
        )
    return render(request, "adminCart.html", context={"products": data})


def logout(request):
    LoadStorage.objects.all().delete()
    return index(request)


def checkout(request):
    data = {}
    if request.method == "POST":
        name = request.POST.get("name", "")
        qty = request.POST.get("qty", "")
        cost = request.POST.get("cost", "")
        image = request.POST.get("image", "")
        id = request.POST.get("id", "")
        imageId = request.POST.get("imageId", "")
        data = {
            "name": name,
            "qty": qty,
            "cost": cost,
            "image": image,
            "id": id,
            "imageId": imageId,
        }
    return render(request, "checkOut.html", data)


def checkOutSubmit(request):
    if request.method == "POST":
        pname = request.POST.get("pname", "")
        image = request.POST.get("imageId", "")
        status = request.POST.get("status", "")
        qty = request.POST.get("qty", "")
        cost = request.POST.get("cost", "")
        total = request.POST.get("total", "")
        userdata = LoadStorage.objects.all()
        user = userdata.last()
        contract_purchase.functions.setData(
            user.name,
            user.mobile,
            user.email,
            user.address,
            pname,
            image,
            "Pending",
            int(qty),
            int(cost),
            int(total),
        ).transact(
            {
                "from": app_user,
                "nonce": web3.eth.get_transaction_count(app_user),
                "gas": 600000,
            }
        )
        return index(request)


def UserHistory(request):
    userData = LoadStorage.objects.all().first().email
    id, name, mobile, email, addresses, pname, image, status, qty, cost, total = contract_purchase.functions.getAccordingToUser(userData).call(
            {"from": app_user}
        )
    
    data = []
    for i in range(len(id)):
        if userData in email[i]: 
            imageNothing = ImageModel.objects.get(time=image[i])
            data.append(
            {
                "id": id[i],
                "name": name[i],
                "mobile": mobile[i],
                "email": email[i],
                "addresses": addresses[i],
                "pname": pname[i],
                "image": f"data:image/png;base64,{imageNothing.image_base64}",
                "status": status[i],
                "qty": qty[i],
                "cost": cost[i],
                "total": total[i],
            }
        )
    return render(request, "userHistory.html", context={"history": data})


def profile(request):
    details = LoadStorage.objects.get()
    
    userData = LoadStorage.objects.all().first().email
    id, name, mobile, email, addresses, pname, image, status, qty, cost, total = contract_purchase.functions.getAccordingToUser(userData).call(
            {"from": app_user}
        )
    
    data2 = []
    for i in range(len(id)):
        if userData in email[i]:
            print('lkjklj') 
            imageNothing = ImageModel.objects.get(time=image[i])
            data2.append(
            {
                "id": id[i],
                "name": name[i],
                "mobile": mobile[i],
                "email": email[i],
                "addresses": addresses[i],
                "pname": pname[i],
                "image": f"data:image/png;base64,{imageNothing.image_base64}",
                "status": status[i],
                "qty": qty[i],
                "cost": cost[i],
                "total": total[i],
            }
        )
            
    return render(request, "userProfile.html",context= {
         "name": details.name,
        "password": details.password,
        "mobile": details.mobile,
        "address": details.address,"history":data2})


def updateProfile(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        address = request.POST.get("address", "")
        mobile = request.POST.get("mobile", "")
        address = request.POST.get("address", "")
        password = request.POST.get("password", "")
        userid = LoadStorage.objects.get().id
        contract.functions.updateUser(name, address, mobile, password, userid).transact(
            {
                "from": app_user,
                "nonce": web3.eth.get_transaction_count(app_user),
                "gas": 600000,
            }
        )
        data = LoadStorage.objects.get(id=userid)
        data.email = name
        data.address = address
        data.mobile = mobile
        data.password = password
        data.save()
        return index(request)


def submitUpdate(request):
    if request.method == "GET":
        image = request.GET.get("imageId", 0)
        qty = request.GET.get("qty", 0)
        id = request.GET.get("id", 0)
        status=request.GET.get("status","")
        id2, imageId, name, qty1, cost = contract_product.functions.getProducts(
            app_user
        ).call()
        for i in range(len(qty1)):
            # print(image)
            if image == imageId[i]:
                if int(qty) < qty1[i]:
                    contract_purchase.functions.updatePurchase(
                        status, int(id)
                    ).transact({"from": app_user})
                    # print(Nothing)
                    contract_product.functions.stateUpdate(
                        "Decreament", int(id2[i]), int(qty)
                    ).transact({"from": app_user})
                    return JsonResponse(data={
                        'error':True,
                        "message":'Success'
                    })
        return  JsonResponse(data={
                        'error':True,
                        "message":'In Sufficient Qty'
                    })


def adminWithMessage(request, nothing):
    data = []
    id, name, mobile, email, addresses, pname, image, status, qty, cost, total = (
        contract_purchase.functions.getDataHistory().call({"from": app_user})
    )
    for i in range(len(id)):
        photo = ImageModel.objects.get(time=image[i])
        if str(id[i]) == nothing["id"]:
            data.append(
                {
                    "id": id[i],
                    "message": "InSufficient Qty",
                    "name": name[i],
                    "mobile": mobile[i],
                    "email": email[i],
                    "addresses": addresses[i],
                    "pname": pname[i],
                    "image": f"data:image/png;base64,{photo.image_base64}",
                    "status": status[i],
                    "qty": qty[i],
                    "cost": cost[i],
                    "total": total[i],
                    "imageId": image[i],
                }
            )
        else:
            data.append(
                {
                    "id": id[i],
                    "name": name[i],
                    "mobile": mobile[i],
                    "email": email[i],
                    "addresses": addresses[i],
                    "pname": pname[i],
                    "image": f"data:image/png;base64,{photo.image_base64}",
                    "status": status[i],
                    "qty": qty[i],
                    "cost": cost[i],
                    "total": total[i],
                    "imageId": image[i],
                }
            )
    return render(request, "adminCart.html", context={"products": data})


def updateQty(request):
    if request.method == "POST":
        id2 = request.POST.get("idPoint", 0)
        qty2 = request.POST.get("qty", 0)
        state = request.POST.get("state", "")
        id, image, name, qty, cost = contract_product.functions.getProducts(
            app_user
        ).call()
        data = []
        for i in range(len(name)):
            imageFrom = ImageModel.objects.get(time=image[i])
            data.append(
                {
                    "id": id[i],
                    "image": f"data:image/png;base64,{imageFrom.image_base64}",
                    "name": name[i],
                    "qty": qty[i],
                    "cost": cost[i],
                }
            )

        if state == "Decreament":
            for i in range(len(name)):
                if id[i] == int(id2) and int(qty[i]) >= int(qty2):
                    contract_product.functions.stateUpdate(
                        str(state), int(id2), int(qty2)
                    ).transact({"from": app_user})
                    print(f"{id2}   {id}")
                    return viewItems(request)
                else:
                    """"""
            return render(
                request,
                "adminViewItems.html",
                context={
                    "products": data,
                    "message": "Quantity Should be less than according to the Current Quantity",
                },
            )
        elif state == "Increament":
            contract_product.functions.stateUpdate(
                str(state), int(id2), int(qty2)
            ).transact({"from": app_user})
            print(f"{id2}   {id}")
            return viewItems(request)


def searchOrder(request):
    if request.method=="GET":
        search=request.GET.get("search","")
        data = []
        id, name, mobile, email, addresses, pname, image, status, qty, cost, total = (
        contract_purchase.functions.getDataHistory().call({"from": app_user})
        )
        for i in range(len(id)):
                if search in str(id[i]): 
                    photo = ImageModel.objects.get(time=image[i])
                    data.append({
                "id": id[i],
                "name": name[i],
                "mobile": mobile[i],
                "email": email[i],
                "addresses": addresses[i],
                "pname": pname[i],
                "image": f"data:image/png;base64,{photo.image_base64}",
                "status": status[i],
                "qty": qty[i],
                "cost": cost[i],
                "total": total[i],
                "imageId": image[i],
            })
        return JsonResponse(data={"error":True,'data':data})