
def ok(data=None,message="success",code=0):
    return {"code":code,"message":message,"data":data}

def fail(message="false",code=1):
    return {"code":code,"message":message,"data":None}


