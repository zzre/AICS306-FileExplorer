import os
import requests
import hashlib
import magic
import sqlite3

class VirusChecker:
    initialized = False
    conn = None
    cursor = None
    
    def __init__(self, API_KEY=''):
        # VirusTotal API
        self.URL = "https://www.virustotal.com/api/v3"
        self.GUI_URL = "https://www.virustotal.com/gui/file"
        self.API_KEY = API_KEY
        self._initialize()

    @classmethod
    def _initialize(cls):
        if not cls.initialized:
            cls.conn = sqlite3.connect('VirusCheck.db')
            cls.cursor = cls.conn.cursor()
            cls.cursor.execute('''
                CREATE TABLE IF NOT EXISTS VirusCheck (
                    filename TEXT PRIMARY KEY,
                    score TEXT,
                    chkDate DATE,
                    isMalicious BOOLEAN NOT NULL,
                    url TEXT
                )
            ''')
            cls.conn.commit()

    def uploadFile(self, filepath):
        '''
        VirusTotal에 검사할 파일 업로드

        References:
        - https://docs.virustotal.com/reference/files-scan
        - https://docs.virustotal.com/reference/files-upload-url

        parameters:
        - filepath: 파일 경로
        '''

        if os.path.getsize(filepath) >= 32*1024*1024:
            # 대용량 파일 업로드 URL 요청
            headers = {
                "accept": "application/json",
                "x-apikey": self.API_KEY
            }
            res = requests.get(f"{self.URL}/files/upload_url", headers=headers)
            if res.status_code != 200:
                raise ValueError(f"파일 업로드 URL 요청 실패: {res.status_code}")

            URL = res.json()['data']
        else:
            URL = f'{self.URL}/files'

        # 파일 업로드
        with open(filepath, "rb") as f:
            mimeType = magic.from_buffer(f.read(2048), mime=True)
            f.seek(0)

            files = { "file": (os.path.basename(filepath), open(filepath, "rb"), mimeType) }
            headers = {
                "accept": "application/json",
                "x-apikey": self.API_KEY
            }

            return requests.post(URL, files=files, headers=headers)

    def getAnalysis(self, filepath, uploaded=True):
        '''
        바이러스 탐지 결과 반환

        parameters:
        - filepath: 바이러스 탐지 결과를 확인할 파일 경로
        - uploaded: 과거 파일 업로드 여부
        '''

        if uploaded:
            with open(filepath, "rb") as f:
                data = f.read()
                filehash = hashlib.sha256(data).hexdigest()    
        else:
            res = self.uploadFile(filepath)
            filehash = res['data']['id']

        headers = {
            "accept": "application/json",
            "x-apikey": self.API_KEY
        }
        return requests.get(f'{self.URL}/files/{filehash}', headers=headers)

    def loadAPIKey(self, keyFile):
        '''
        keyFile로부터 API_KEY 로드

        parameters:
        - keyFile: API_KEY가 적힌 파일 경로
        '''

        with open(keyFile, 'r') as f:
            self.API_KEY = f.read().strip()

    def storeResult(self, filepath, score, date, isMalicious, filehash):
        '''
        DB에 검사 결과 저장

        parameters:
        - filepath: 검사한 파일 경로
        - score: `(악성 파일로 탐지한 엔진 수)/(전체 엔진 수)`
        - date: 바이러스 검사 날짜
        - isMalicious: 파일의 검사 결과
        '''

        self.cursor.execute("INSERT INTO VirusCheck (filename, score, chkDate, isMalicious, url) VALUES (?, ?, ?, ?, ?)", (filepath, score, date, isMalicious, f'{self.GUI_URL}/{filehash}'))
        self.conn.commit()

    def getFileStatus(self, filepath):
        '''
        DB에 저장된 검사 결과 가져오기

        parameters:
        - filepath: 바이러스 검사 결과를 가져올 파일 경로
        '''

        self.cursor.execute("SELECT score, chkDate, isMalicious, url FROM VirusCheck WHERE filename = ?", (filepath,))
        res = self.cursor.fetchone()
        
        if res:
            checked = True
            score = res[0]
            date = res[1]
            isMalicious = res[2]
            url = res[3]
        else:
            checked = False
            score = None
            date = None
            isMalicious = None
            url = None

        return (checked, score, date, isMalicious, url)
