import hashlib 
class Voter:

    def __init__(self,email,name) -> None:
        self.email = email 
        self.hashPw = None
        self.name = name
        self.transAddress  = None 
        self.verifiedForVote = False

    def setVerified(self) -> None:
        self.verifiedForVote = True

    def setTransparentAddress(self,address) -> None:
        self.transAddress = address
        
    def setPassword(self,pw) -> None:
        pw = bytes(pw,'utf-8')
        email_bytes = bytes(self.email,'utf-8')
        self.hashPw = hashlib.pbkdf2_hmac('sha256',pw,email_bytes,1000)

    def checkPassword(self,pw) -> bool:
        pw = bytes(pw,'utf-8')
        email_bytes = bytes(self.email,'utf-8')
        return hashlib.pbkdf2_hmac('sha256',pw,email_bytes,1000) == self.hashPw
    
    def getTransparentAddress(self) -> str:
        return self.transAddress

    def getEmail(self) -> str:
        return self.email

    def getname(self) -> str:
        return self.name

    def getVerificationForVote(self) -> bool:
        return self.verifiedForVote
    