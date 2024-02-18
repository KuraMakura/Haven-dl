import json, math, os, requests, shutil, time

assetTypeNames = ["hdris", "textures", "models"]
assetTypeSizes = []
for i in assetTypeNames: assetTypeSizes.append(0)

def formatTime(t): return "{} hr {:02d} min {:02d} sec".format(math.floor(t / 3600.0), math.floor(t / 60.0) % 60, math.floor(t % 60))

def formatBytes(b): return "{} GB".format(math.ceil(b / 1073741824))

def downloadFile(path, file, type, checkSize):
    if not checkSize:
        url = file["url"]
        data = requests.get(url).content
        if not os.path.exists(path): os.makedirs(path)
        file = open(path + "/" + url.split("/")[-1], "wb")
        file.write(data)
        file.close()
    else: assetTypeSizes[type] += file["size"]

def downloadAsset(files, name, type, resolutions, path, checkSize):
    for resNum, res in enumerate(resolutions):
        if verbosity >= 2 and not checkSize: print("Downloading {}...".format(res))

        if type == 0: downloadFile(path, files["hdri"][res][hdriFormat], type, checkSize) #HDRI

        elif type == 1 or type == 2: #Texture or Model
            if resNum == 0: downloadFile(path, files["blend"][res]["blend"], type, checkSize)
            for tex in files:
                try: downloadFile(path + "/textures", files[tex][res][textureFormat], type, checkSize)
                except KeyError: continue

        else: print("ERROR: Unknown asset type {}; Unable to download.".format(type)) #Unknown

def runAll(checkSize):
    startTime = time.time()
    timeElapsed = 0

    for assetNum, name in enumerate(fullList):
        asset = fullList[name]
        assetType = asset["type"]
        assetTypeName = assetTypeNames[assetType]

        path = downloadLocation + "/" + assetTypeName + "/" + name
        if os.path.exists(path):
            if verbosity >= 2: print("Asset already downloaded; Skipping...") 
            continue

        files = requests.get("https://api.polyhaven.com/files/" + name).json()

        timeElapsed = time.time() - startTime
        avgTime = timeElapsed / (assetNum + 1)

        if verbosity >= 1:
            print("Time elapsed: {} | ETA: {}".format(formatTime(timeElapsed), formatTime((numAssets - assetNum) * avgTime)))
            if not checkSize:
                print("Asset {} of {} [{}]".format(assetNum + 1, numAssets, name))
                if verbosity >= 3: print(url)

        downloadAsset(files, name, assetType, downloadResolutions[assetTypeName], path, checkSize)

        if not checkSize: print("")

    if verbosity >= 1: print("\nFinished in " + formatTime(timeElapsed))

#Load settings
settings = json.load(open("settings.json", "r"))
skipStorageCheck    = settings["skipStorageCheck"]
downloadLocation    = settings["downloadLocation"]
downloadResolutions = settings["downloadResolutions"]
hdriFormat          = settings["hdriFormat"]
textureFormat       = settings["textureFormat"]
normalMapStandard   = settings["normalMapStandard"]
verbosity           = settings["consoleOutputVerbosity"]

if verbosity >= 1: print("Haven-dl v24.02.18\nPlease consider supporting Poly Haven if you are able to\nhttps://patreon.com/polyhaven/overview\n")

#Retrieve list of assets
fullList = requests.get("https://api.polyhaven.com/assets").json()

numAssets = len(fullList)
if verbosity >= 1: print("Found {} assets\n".format(numAssets))

if skipStorageCheck == "no":
    print("Checking storage requirements...\n")
    runAll(True)

    size = 0
    for i in assetTypeSizes: size += i
    if verbosity >= 1: print("Total size: " + formatBytes(size) + "\n")

    free = shutil.disk_usage(downloadLocation[:2]).free

    if free < size: print("Insufficient storage space: " + formatBytes(free))
    else: runAll(False)

else: runAll(False)
