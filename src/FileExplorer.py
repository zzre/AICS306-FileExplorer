import os
import shutil
import subprocess
from datetime import datetime
import zipfile
import magic
from VirusChecker import VirusChecker
import json
import sys

class FileExplorer:
    def __init__(self, path=os.path.abspath(os.getcwd()), virusChecker=VirusChecker('5963ec8ffd5d88f1b8a059f4cb40ec34f95660a0500aff88bb5cd7577373a44e'), updateCallback=lambda: None):
        '''
        파일 탐색기 초기화

        parameters
        - path: 탐색할 디렉터리의 절대 경로
        - updateCallback: 파일 목록이 업데이트될 때 호출될 콜백 함수
        '''

        self.prevPaths = []
        self.nextPaths = []
        self.currentPath = path
        self.updateCallback = updateCallback
        self.currentFileList = [] # 현재 보여지는 파일 이름, 수정한 날짜, 유형, 크기 목록, 바이러스 검사 여부
        self.virusChecker = virusChecker

        if hasattr(sys, '_MEIPASS'):
            jsonPath = os.path.join(sys._MEIPASS, "assets", "data", "mimetype.json")
        else:
            jsonPath = f'{os.path.dirname(__file__)}\\..\\assets\\data\\mimetype.json'
        with open(jsonPath, 'r') as f:
            self.mimetype = json.load(f)
    
    def listDirectory(self, path=''):
        '''
        디렉터리 목록 조회

        parameters
        - path: 목록을 조회할 디렉터리 경로
        '''

        def isJunction(path):
            try:
                return bool(os.readlink(path))
            except OSError:
                return False
        
        # 인자로 전달된 path가 없으면 self.currentPath 경로의 디렉터리 목록 조회
        if path == '':
            path = self.currentPath

        self.updateCurrentFileList([p for p in os.listdir(path) if not isJunction(p)])
        self.updateCallback(self.currentFileList)
    
    def changeDirectory(self, newPath):
        '''
        디렉터리 변경

        parameters:
        - newPath: 이동할 디렉터리 경로
        '''

        if os.path.isdir(newPath):
            self.prevPaths.append(self.currentPath)
            self.currentPath = os.path.abspath(newPath)
            os.chdir(self.currentPath)
            self.listDirectory()

    def changeToPrevDirectory(self):
        '''
        이전에 위치했던 디렉터리로 이동
        '''

        if len(self.prevPaths) > 0:
            self.nextPaths.append(self.currentPath)
            self.currentPath = self.prevPaths.pop()
            os.chdir(self.currentPath)
            self.listDirectory()

    def changeToNextDirectory(self):
        '''
        앞에 위치했던 디렉터리로 이동
        '''

        if len(self.nextPaths) > 0:
            self.prevPaths.append(self.currentPath)
            self.currentPath = self.nextPaths.pop()
            os.chdir(self.currentPath)
            self.listDirectory()
        
    def changeToParentDirectory(self):
        '''
        부모 디렉터리로 이동
        '''

        os.chdir(f'{self.currentPath}\\..')
        newPath = os.getcwd()

        # 이미 root directory에 있었는지 확인
        if newPath != self.currentPath:
            self.changeDirectory(newPath)
            self.listDirectory()

    def makeDirectory(self, directoryName):
        '''
        디렉터리 생성

        parameters:
        - directoryName: 생성할 디렉터리 명
        '''

        invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        if directoryName == '..':
            raise ValueError(f'잘못된 디렉터리명: ..')

        if any(c in directoryName for c in invalidChars):
            raise ValueError(f"디렉터리 이름에 허용되지 않는 문자가 있습니다: {invalidChars}")
        
        os.mkdir(directoryName)
        self.listDirectory()
    
    def removeDirectory(self, directoryName):
        '''
        디렉터리 생성

        parameters:
        - directoryName: 삭제할 디렉터리명
        '''
        
        shutil.rmtree(directoryName) 
        self.listDirectory()
    
    def renameFile(self, oldName, newName):
        '''
        파일 이름 변경

        parameters:
        - oldName: 기존 파일명
        - newName: 새 파일명
        '''

        invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

        if newName == '..':
            raise ValueError(f'잘못된 파일명: ..')

        if any(c in newName for c in invalidChars):
            raise ValueError(f"파일 이름에 허용되지 않는 문자가 있습니다: {invalidChars}")

        os.rename(oldName, newName)
        self.listDirectory()
    
    def remove(self, filename):
        if os.path.isdir(filename):
            self.removeDirectory(filename)
        else:
            self.removeFile(filename)

    def renameDirectory(self, oldName, newName):
        '''
        디렉터리 이름 변경

        parameters:
        - oldName: 기존 디렉터리명
        - newName: 새 디렉터리명
        '''

        invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        if newName == '..':
            raise ValueError(f'잘못된 디렉터리명: ..')

        if any(c in newName for c in invalidChars):
            raise ValueError(f"디렉터리 이름에 허용되지 않는 문자가 있습니다: {invalidChars}")

        os.rename(oldName, newName)
        self.listDirectory()

    def copyFiles(self, files, destPath):
        '''
        파일/폴더 복사

        parameters:
        - files: 파일/폴더 목록 (절대 경로)
        - destPath: 파일/폴더를 복사할 경로
        '''

        # 선택된 파일에 대해 모두 복사
        for file in files:
            filename = os.path.basename(file)
            if os.path.exists(filename):
                filename, ext = os.path.splitext(filename)
                i = 1
                while True:
                    if not os.path.exists(f'{filename} ({i}){ext}'):
                        break
                    i += 1
                filename = f'{filename} ({i}){ext}'

            # 폴더를 복사하는 경우 하위 파일까지 복사
            if os.path.isdir(file):
                shutil.copytree(file, os.path.join(destPath, filename), dirs_exist_ok=True)
            
            # 파일만 복사하는 경우
            else:
                shutil.copy(file, os.path.join(destPath, filename))

        self.listDirectory()

    def getAttribute(self, filename):
        '''
        파일/폴더 속성 가져오기

        parameters:
        - filename: 속성을 가져올 파일 이름
        '''

        # 파일 형식
        if os.path.isdir(filename):
            fileFormat = '폴더'
        else:
            fileFormat = self.getFileFormat(filename)

        # 위치 (절대 경로)
        filepath = os.path.abspath(filename)

        # 파일 크기
        size = os.path.getsize(filename)
        if size < 1024:
            size = f"{size:,} bytes"
        else:
            size = f"{size/1024:,.1f} KB"

        # 생성 날짜
        ctime = os.path.getctime(filename)
        ctime = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d')

        # 수정 날짜
        mtime = os.path.getmtime(filename)
        mtime = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

        # 확장자
        if os.path.isdir(filename):
            filetype = "폴더"
        elif os.path.splitext(filename)[1]:
            # 확장자가 있는 경우 파일 유형을 확장자로 설정
            filetype = os.path.splitext(filename)[1][1:] + " 파일"
        else:
            filetype = "파일"

        # 바이러스 토탈 검사 결과/날짜
        checked, score, chkDate, isMalicious, url = self.virusChecker.getFileStatus(os.path.abspath(filename))
        if not checked:
            score = '-'
            chkDate = '-'
            url = None
        
        return fileFormat, filepath, size, ctime, mtime, filetype, score, chkDate, url

    def makeFile(self, filename):
        '''
        빈 파일 생성

        parameters:
        - filename: 생성할 파일 이름
        '''

        invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        if filename == '..':
            raise ValueError(f'잘못된 파일명: ..')

        if any(c in filename for c in invalidChars):
            raise ValueError(f"파일 이름에 허용되지 않는 문자가 있습니다: {invalidChars}")

        if os.path.exists(filename):
            raise ValueError(f"같은 이름의 파일이 이미 존재합니다: {filename}")
        
        # 빈 파일 생성
        with open(filename, "w") as f:
            pass

        self.listDirectory()

    def removeFile(self, filename):
        '''
        파일 삭제

        parameters:
        - filename: 삭제할 파일명
        '''
        
        os.remove(filename)
        self.listDirectory()
    
    def removeFiles(self, filenames):
        '''
        다중 파일 삭제

        parameters:
        - filenames: 삭제할 파일 목록
        '''

        for filename in filenames:
            if os.path.isdir(filename):
                self.removeDirectory(filename)
            else:
                self.removeFile(filename)

        self.listDirectory()

    def moveFiles(self, filenames, destDirectory):
        '''
        다중 파일 이동

        parameters:
        - filenames: 이동할 파일 목록
        '''

        for filename in filenames:
            dest = f'{destDirectory}\\{os.path.basename(filename)}'
            
            if os.path.exists(dest):
                prefix, suffix = os.path.splitext(dest)
                i = 1
                while True:
                    if not os.path.exists(f'{prefix} ({i}){suffix}'):
                        break
                    i += 1
                dest = f'{prefix} ({i}){suffix}'
            
            shutil.move(filename, suffix)

        self.listDirectory()

    def startFile(self, filename):
        '''
        파일을 연결 프로그램으로 열기

        parameters
        - filename: 실행할 파일의 절대 경로
        '''

        if os.path.isabs(filename):
            # os.startfile을 이용하면 연결 프로그램이 없는 프로그램에 대한 처리가 안 됨
            subprocess.run(['explorer.exe', filename])
        else:
            raise ValueError(f'주어진 파일 경로가 절대 경로가 아닙니다: {filename}')

    def getFileFormat(self, filename, mime=True):
        '''
        파일 포맷 가져오기

        parameters:
        - filename: 파일 포맷을 가져올 파일 이름
        '''

        if os.path.exists(filename):
            # magic.from_file은 경로에 unicode 문자열이 있는 경우 에러 발생
            return magic.from_buffer(open(filename, 'rb').read(2048), mime=mime)

    
    def checkFileFormatMismatch(self, filename, mime=True):
        _, ext = os.path.splitext(filename)

        fileFormat = self.getFileFormat(filename, mime)
        expectedExt = self.mimetype.get(fileFormat)
        # print(f'{filename}: {fileFormat} - {expectedExt}')

        if isinstance(expectedExt, list):
            return ext.lower() not in expectedExt
        else:
            return ext.lower() != expectedExt

    def searchFile(self, searchText, recursive=True):
        '''
        파일 검색하기

        parameters:
        - searchText: 검색할 문자열
        - recursive: 하위 폴더도 검색 범위에 포함할지 여부
        '''

        res = []
        def dfs(curPath, recursive):
            # curPath의 파일에 대해 문자열 검색
            for filename in os.listdir(curPath):
                # filename에 검색 문자열이 존재하는 경우 검색 결과에 포함
                if searchText in filename:
                    res.append(os.path.relpath(f'{curPath}\\{filename}', self.currentPath))
                
                # 재귀적으로 검색하는 경우 하위 디렉터리에 대해서도 검색 수행
                if recursive and os.path.isdir(f'{curPath}\\{filename}'):
                    dfs(f'{curPath}\\{filename}', recursive)

        dfs(self.currentPath, recursive)

        return res
    
    def updateCurrentFileList(self, files):
        '''
        보여질 파일 이름, 수정한 날짜, 유형, 크기 목록 업데이트

        parameters:
        - files: 보여줄 파일 목록
        '''

        self.currentFileList.clear()

        for filename in files:
            # 수정 날짜
            mtime = os.path.getmtime(filename)
            date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

            # 파일 유형
            if os.path.isdir(filename):
                filetype = "폴더"
            elif os.path.splitext(filename)[1]:
                # 확장자가 있는 경우 파일 유형을 확장자로 설정
                filetype = os.path.splitext(filename)[1][1:] + " 파일"
            else:
                filetype = "파일"

            # 파일 크기
            size = os.path.getsize(filename)
            if size < 1024:
                size = f"{size:,} bytes"
            else:
                size = f"{size/1024:,.1f} KB"

            # 바이러스 검사 여부
            checked, score, chkDate, isMalicious, url = self.virusChecker.getFileStatus(os.path.abspath(filename))

            # 파일 포맷 검사
            try:
                if os.path.isdir(filename):
                    badType = False
                else:
                    badType = self.checkFileFormatMismatch(filename)
            except:
                badType = None # 권한 부족

            self.currentFileList.append([filename, date, size, filetype, isMalicious, badType])

    def virusCheck(self, filename):
        '''
        VirusTotal을 통해 바이러스 검사 결과 받아오기

        parameters:
        - filename: 검사할 파일명
        '''

        filepath = os.path.abspath(filename)
        checked, score, date, isMalicious, url = self.virusChecker.getFileStatus(filepath)
        if checked:
            return score, date, isMalicious
        else:
            res = self.virusChecker.getAnalysis(filepath)
            try:
                res = json.loads(res.text)['data']
                filehash = res['id']
                res = res['attributes']['last_analysis_stats']
                malicious = res['malicious'] + res['suspicious']
                harmless = res['undetected'] +  res['harmless']
                score = f'{malicious}/{malicious + harmless}'
                isMalicious = malicious > harmless
                self.virusChecker.storeResult(filepath, score, datetime.today().strftime('%Y-%m-%d'), isMalicious, filehash)
                return score, date, isMalicious
            except:
                self.virusChecker.storeResult(filepath, '?', datetime.today().strftime('%Y-%m-%d'), False, '')
                return '?', datetime.today().strftime('%Y-%m-%d'), -1

    def getCurrentFileList(self):
        '''
        currentFileList 반환
        '''

        return self.currentFileList

    def getCurrentPath(self):
        '''
        currentPath 반환
        '''
        
        return self.currentPath

    def sortFiles(self, sortType):
        '''
        파일 정렬

        parameters:
        - sortType: 정렬 형식
        '''

        raise NotImplementedError("FileExplorer.sortFiles")
    
    def zipFiles(self, files, zipName):
        '''
        파일/폴더 압축

        parameters:
        - files: 압축할 파일 목록
        - zipName: .zip 파일 이름
        '''

        invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

        if any(c in zipName for c in invalidChars):
            raise ValueError(f"파일 이름에 허용되지 않는 문자가 있습니다: {invalidChars}")

        if zipName.lower().endswith(".zip"):
            zipName = zipName[:-4]

        if os.path.exists(zipName):
            i = 1
            while True:
                if not os.path.exists(f'{zipName} ({i}).zip'):
                    break
                i += 1
            zipName = f'{zipName} ({i}).zip'

        with zipfile.ZipFile(zipName, 'w', zipfile.ZIP_DEFLATED) as f:
            for file in files:
                if os.path.isdir(file):
                    # 하위 폴더를 순회하며 파일을 zip에 추가
                    for basepath, _, filenames in os.walk(file):
                        for filename in filenames:
                            abspath = os.path.join(basepath, filename)
                            f.write(abspath, os.path.relpath(abspath, self.currentPath))
                else:
                    f.write(file, os.path.basename(file))

        self.listDirectory()

    def extractFile(self, zipName):
        '''
        zip 파일 압축 해제

        parameters:
        - zipName: 압축 해제할 zip 파일
        '''

        outputFolder = zipName

        if outputFolder.lower().endswith(".zip"):
            outputFolder = outputFolder[:-4]

        if os.path.exists(outputFolder):
            i = 1
            while True:
                if not os.path.exists(f'{outputFolder} ({i}).zip'):
                    break
                i += 1
            outputFolder = f'{outputFolder} ({i}).zip'

        with zipfile.ZipFile(zipName, 'r') as f:
            os.makedirs(outputFolder)
            f.extractall(outputFolder)

        self.listDirectory()
