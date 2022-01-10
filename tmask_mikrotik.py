#!/usr/bin/python

__author__ = "biuro@tmask.pl"
__copyright__ = "Copyright (C) 2022 TMask.pl"
__license__ = "MIT License"
__version__ = "1.0"

# pip3 install paramiko
import paramiko
import time
import fnmatch
import os
import csv

local_bkp_path = 'bkp'

if not os.path.exists(local_bkp_path):
    os.makedirs(local_bkp_path)
    
# Otwórz plik csv z hostami i pobierz BKP
def getHostsMt(local_path_file):
    with open(local_path_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            if not str(row).startswith('#'):
                col = row[0].split(';')
                hostname = col[0].replace("'","")
                username = col[1].replace("'", "")
                password = col[2].replace("'", "")
                port = col[3].replace("'", "")
            
                try:
                    createBackupAndRscMt(hostname, username, password, port)
                    getFilesWithMt(hostname, username, password, port, local_bkp_path)
                except:
                    pass

# Kasuj stary backup
def delOldBkpMt(local_path_file):
    with open(local_path_file, 'r') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            col = row[0].split(';')
            hostname = col[0].replace("'", "")
            username = col[1].replace("'", "")
            password = col[2].replace("'", "")
            port = col[3].replace("'", "")
            
            try:
                delFilesWithMt(hostname, username, password, port)
            except:
                pass

# Stworzenie backup i rsc
def createBackupAndRscMt(hostname, username, password, port):
    now = time.strftime("%Y-%m-%d_%H-%M")
    try: 
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username,
                    password=password, port=port, allow_agent=False, look_for_keys=False)

        stdin, stdout, stderr = ssh.exec_command(f'/system backup save dont-encrypt=yes name={hostname}_{now}.backup')
        print(f'Host - {hostname} - Create file --> {hostname}_{now}.backup')
        time.sleep(1)
        stdin, stdout, stderr = ssh.exec_command(f'/')
        stdin, stdout, stderr = ssh.exec_command(f'/export file={hostname}_{now}.rsc')
        print(f'Host - {hostname} - Create file --> {hostname}_{now}.rsc')
        time.sleep(1)
    except:
        pass
    finally:
        ssh.close()
        
    
# Pobierz pliki z Mikrotik
def getFilesWithMt(hostname, username, password, port, local_bkp_path):
    now = time.strftime("%Y-%m-%d_%H-%M")
    try: 
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username,
                    password=password, port=port, allow_agent=False, look_for_keys=False)
        sftp_client = ssh.open_sftp()

        for filename in sftp_client.listdir('/'):
            if fnmatch.fnmatch(filename, "*.backup"):
                print(f'Host - {hostname} - Download file --> {filename}')
                sftp_client.get(filename, os.path.join(local_bkp_path, filename))
            if fnmatch.fnmatch(filename, "*.rsc"):
                print(f'Host - {hostname} - Download file --> {filename}')
                sftp_client.get(filename, os.path.join(local_bkp_path, filename))
                
    except:
        pass
    finally:
        sftp_client.close()
        ssh.close()
        
    # delFilesWithMt(hostname, username, password, port)
    
# Usuń stare pliki backup Mikrotik
def delFilesWithMt(hostname, username, password, port):
    now = time.strftime("%Y-%m-%d_%H-%M")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username,
                    password=password, port=port, allow_agent=False, look_for_keys=False)
        
        sftp_client = ssh.open_sftp()
        list = []
        for filename in sftp_client.listdir('/'):
            if not fnmatch.fnmatch(filename, "auto-before-reset.backup"):
                if fnmatch.fnmatch(filename, "*.backup") or fnmatch.fnmatch(filename, "*.rsc"):
                    list.append(filename)
        sftp_client.close()

        for l in list:
            stdin, stdout, stderr = ssh.exec_command(f'file remove "{l}"')
            print(f'Host - {hostname} -  Remove file --> {l}')
        ssh.close()
    except:
        pass
    finally:
        pass

# Funkcja główna
def main():
    # getHostsMt('mikrotik.csv')
    delOldBkpMt('mikrotik.csv')

if __name__ == "__main__":
    main()
