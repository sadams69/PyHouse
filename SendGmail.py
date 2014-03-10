import smtplib
from PrivateHouse import PrivateHouseEmail
from email.mime.text import MIMEText as text

def Send(msg = 'Test' , to = PrivateHouseEmail['to']):  
    fromaddr = PrivateHouseEmail['from'] 
    toaddrs  = to  
  
    # Credentials (if needed)  
    username = PrivateHouseEmail['username']  
    password = PrivateHouseEmail['password']
    # I'm sure that this breaks every security rule ever made. But right now this is all I know how to do. 
    # PrivateHouse
   
    m = text(msg)
    m['Subject'] = 'HousePi Door Alert'
    m['From'] = fromaddr
    m['To'] = toaddrs


    # The actual mail send  
    server = smtplib.SMTP('smtp.gmail.com:587')  
    server.starttls()  
    server.login(username,password)
    print 'From: %s' % fromaddr
    print 'to: %s' % toaddrs
    print msg
    
    server.sendmail(fromaddr, toaddrs, m.as_string())  
    server.quit()

if __name__ == '__main__':
    Send('Hey', to = 'JohnDoe@gmail.com')
    
