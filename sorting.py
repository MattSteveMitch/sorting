import pygame
import random
import time
import array

ARRAY_SIZE = 600
BOGO_SIZE = 8
MAX_INT = 5000
SPF_DEFAULT = 30
FPS = 120
stepsPerFrame = SPF_DEFAULT

frameCounter = 0
startTime = 0.0
frameStart = 0.0
skip = False
previous = False
order = 0

ARRAY_HEIGHT = 300
ARRAY_Y_POS = ARRAY_HEIGHT + 50

updateAll = pygame.display.update

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
pygame.init()

comparedElems = [-1, -1, -1]

pygame.mixer.set_reserved(3)
explodeChannel = pygame.mixer.Channel(0)
beepChannel1 = pygame.mixer.Channel(1)
beepChannel2 = pygame.mixer.Channel(2)
sortIndex = 0

BEEP_AMPLITUDE = 2024
BEEP_DURATION = 0.009

window = pygame.display.set_mode((ARRAY_SIZE + 200, 700))
theArray = [0] * ARRAY_SIZE
bogoArray = [0] * BOGO_SIZE
sortType = ""
PRNG = [0.315244, 0.809516, 0.857341, 0.651020, 0.113699, 0.890160, 0.176477, \
        0.456243, 0.050375, 0.382847, 0.616625, 0.757371, 0.533910, 0.235353, \
        0.966162, 0.542985, 0.351510, 0.038713, 0.513034, 0.916800, 0.178061]
# Yes, I know that Python has a PRNG built in, but I like to make these sorting
# algorithms practical for situations outside of this specific simulation.
# I'm weird like that.
# Anyway, it just seems so wasteful to use Python's RNG, with its massive memory
# overhead, for quicksort when all it needs is just the slightest hint of
# randomness. What if, hypothetically, you're only sorting 20 numbers? Who needs
# 2.5 KiB of overhead memory cost just to sort 20 numbers? And I know I'm already
# using Python's RNG for graphics and such, but again, I'm kinda weird.
PRNGIndex = 0

explodeSound = pygame.mixer.Sound("sorting/explosion2.wav")
explodeSound.set_volume(1.5)

bombs = ["bomb1.png", "bomb2.png", "bomb3.png", "bomb4.png"]
bombFlashing = ["bomb5.png", "bomb6.png", "bomb7.png", "bomb1.png",
                "bomb8.png", "bomb9.png", "bomb10.png", "bomb2.png",
                "bomb11.png", "bomb12.png", "bomb13.png", "bomb3.png"]

explosionimg = pygame.image.load("sorting/explosion.png")
explosionimg = pygame.transform.smoothscale(explosionimg, (20, 20))
bombFrames = []
bombFlashFrames = []

for frame in bombs:
    img = pygame.image.load("sorting/" + frame)
    img = pygame.transform.scale(img, (128, 128))
    bombFrames.append(img)

for frame in bombFlashing:
    img = pygame.image.load("sorting/" + frame)
    img = pygame.transform.scale(img, (128, 128))
    bombFlashFrames.append(img)

bombRect = bombFrames[0].get_rect()
bombRect.center = (int((ARRAY_SIZE + 200) / 2), 350)

explosionRect = explosionimg.get_rect()


class Heap:
    "Don't ask why I made this into an object and literally nothing else. I just don't really care."

    def __init__(self, vals):
        global skip
        self.array = []  # The heap will be stored as an array where the root node is the first element, and
        # each element's children are stored in indices given by (parentIndex * 2) and (parentIndex * 2 + 1)
        self.frame = 0
        self.nonRenderFrame = random.randint(0, 3)
        self.addingStage = True
        self.affectedVals = []
        for val in vals:
            self.addElem(val)
            if skip:
                return

    def size(self):
        return len(self.array)

    def render(self):
        if (self.frame % 4 != self.nonRenderFrame):
            chooseTone(self.affectedVals, False)
            render(True, self.array, True, self.addingStage)

        exitCheck()
        self.frame += 1

    def popTop(self):
        self.nonRenderFrame = random.randint(0, 3)
        topNode = self.array[0]
        self.percolateDown(0)

        return topNode

    def parentInd(self, childInd):
        return int((childInd + 1) / 2) - 1

    def firstChildInd(self, parentInd):
        return (parentInd * 2) + 1

    def secondChildInd(self, parentInd):
        return (parentInd + 1) * 2

    def percolateDown(self, topNodeInd):
        global skip, comparedElems
        arr = self.array

        if skip:
            return

        comparedElems = [-1, -1, -1]
        self.affectedVals = []

        endInd = self.size() - 1

        firstChildIndex = self.firstChildInd(topNodeInd)
        if firstChildIndex > endInd:
            firstChild = None
        else:
            firstChild = arr[firstChildIndex]
            self.affectedVals.append(firstChild)

        secondChildIndex = self.secondChildInd(topNodeInd)
        if secondChildIndex > endInd:
            secondChild = None
        else:
            secondChild = arr[secondChildIndex]
            self.affectedVals.append(secondChild)

        if firstChild == None:  # If this node has no children
            endNode = arr[endInd]
            self.affectedVals = [endNode, arr[topNodeInd]]
            self.render()
            if topNodeInd != endInd:
                # Replace the node with the node that's last in the array
                # (rather than deleting it, because we can't have an empty space in the middle of
                # the array)
                arr[topNodeInd] = endNode
                self.percolateUp(topNodeInd)
            arr.pop()  # Delete last element
            return

        chooseFirstChild = False

        if secondChild == None:
            chooseFirstChild = True
        else:
            comparedElems[0] = firstChildIndex
            comparedElems[1] = secondChildIndex
            if (arr[comparedElems[0]] <= arr[comparedElems[1]]):
                chooseFirstChild = True

        self.render()

        if chooseFirstChild:
            arr[topNodeInd] = firstChild
            self.percolateDown(firstChildIndex)
        else:
            arr[topNodeInd] = secondChild
            self.percolateDown(secondChildIndex)

    def addElem(self, val):
        self.nonRenderFrame = random.randint(0, 3)
        self.array.append(val)
        return self.percolateUp(len(self.array) - 1)

    def percolateUp(self, childInd):
        global skip, comparedElems
        if childInd == 0:
            return

        comparedElems = [-1, -1, -1]

        if skip:
            return

        arr = self.array
        parentInd = self.parentInd(childInd)
        comparedElems[0] = parentInd
        comparedElems[1] = childInd
        parentNode = arr[comparedElems[0]]
        childNode = arr[comparedElems[1]]

        self.affectedVals = [parentNode, childNode]
        self.render()

        if childNode < parentNode:
            arr[childInd] = parentNode
            arr[parentInd] = childNode
            self.percolateUp(parentInd)


def drawExplosion(size):
    global explosionRect
    currImg = pygame.transform.smoothscale(explosionimg, (size, size))
    explosionRect = currImg.get_rect()
    explosionRect.center = bombRect.center
    window.blit(currImg, explosionRect)


def playTone(frequency, duration):
    soundArray = array.array('i', [0] * int(duration * 44100))
    waveLength = int(44100 / frequency)
    quarterWL = int(11025 / frequency)

    for i in range(len(soundArray)):
        placeInWave = i % waveLength
        if placeInWave < quarterWL:
            soundArray[i] = int(placeInWave * (BEEP_AMPLITUDE / quarterWL))
        elif placeInWave > 3 * quarterWL:
            soundArray[i] = int((placeInWave - 3 * quarterWL) * (BEEP_AMPLITUDE / quarterWL)) - BEEP_AMPLITUDE
        else:
            soundArray[i] = int(BEEP_AMPLITUDE - (placeInWave - quarterWL) * (BEEP_AMPLITUDE / quarterWL))

    # print(soundArray)
    sound = pygame.mixer.Sound(soundArray)
    sound.play()


def writeText(message, size, topleft):
    font = pygame.font.SysFont("consolas", size, False)
    textObj = font.render(message, 1, WHITE)
    rectangle = textObj.get_rect()
    rectangle.topleft = topleft
    window.blit(textObj, rectangle)


def intToColor(num, upperLimit):  # Convert an integer between 0 and upperLimit to a color;
    # smaller numbers are closer to red, larger numbers are closer
    # to violet
    if num < upperLimit * 0.2:
        return (255, (num / (upperLimit)) * 5 * 255, 0)
    if num < upperLimit * 0.4:
        return (255 - ((num / upperLimit - 0.2) * 5 * 255), 255, 0)
    if num < upperLimit * 0.6:
        return (0, 255, (num / upperLimit - 0.4) * 5 * 255)
    if num < upperLimit * 0.8:
        return (0, 255 - ((num / upperLimit - 0.6) * 5 * 255), 255)
    else:
        return ((num / upperLimit - 0.8) * 5 * 255, 0, 255)


def chooseTone(writtenVals, includeCompared=True):
    global comparedElems
    comparedTrunc = []  # This array will store only the nonnegative values in comparedElems

    if includeCompared:
        for elem in comparedElems:
            if elem >= 0: comparedTrunc.append(elem)

    number = random.randint(0, len(comparedTrunc) + len(writtenVals) - 1)

    # For this next part, keep in mind that writtenVals is the actual values being
    # selected from, whereas comparedTrunc is the indices of the values in the array
    # being selected from. I'm too lazy to change it.
    if number > len(comparedTrunc) - 1:
        playTone(writtenVals[number - len(comparedTrunc)] + 1, BEEP_DURATION)
    else:
        playTone(theArray[comparedTrunc[number]] + 1, BEEP_DURATION)

def activeSleep(duration):
    global order, previous, skip
    start = time.time()
    while time.time() - start < duration:
        exitCheck()
        if skip:
            if order == 9:
                if previous:
                    return
                else:
                    skip = False
            else:
                if previous:
                    previous = False
                    if order > 0:
                        order -= 2
                    else:
                        order -= 1
                return

def resetArray():
    global sortType, skip, comparedElems, previous
    comparedElems = [-1, -1, -1]
    sortType = "Resetting..."

    for i in range(len(theArray)):
    #    print(skip)
        if i < ARRAY_SIZE / 2:
            newNum = i * 16
        else:
            newNum = (i - ARRAY_SIZE/2) * 16 # Comment out the next line to see what happens when
            # the two halves of the list are sorted, but not the whole thing
        newNum = random.randint(1, MAX_INT)
        theArray[i] = newNum
        exitCheck()
        if (i % int(stepsPerFrame / 8) == 0):
            playTone(newNum + 1, BEEP_DURATION)
            render(True)
            skip = False
            previous = False


def swap(pos1, pos2):
    placeholder = theArray[pos1]
    theArray[pos1] = theArray[pos2]
    theArray[pos2] = placeholder


def checkSorted(startInd, endInd, final, ignoreErrors=False, auxArrayText=False):
    global comparedElems, stepsPerFrame, sortType, skip, order, previous
    auxArray = None
    if auxArrayText:
        auxArray = []
    oldSortType = sortType
    if final:
        sortType = "Scanning for errors..."
    comparedElems[2] = -1
    origFrameSpeed = stepsPerFrame

    if final:
        stepsPerFrame = 4
    else:
        stepsPerFrame = SPF_DEFAULT
    sorted = True
    renderFrame = random.randint(0, stepsPerFrame - 1)
    for comparedElems[0] in range(startInd, endInd - 1):
        comparedElems[1] = comparedElems[0] + 1
        exitCheck()
        if comparedElems[0] % stepsPerFrame == renderFrame:
            chooseTone([])
            render(True, auxArray)
            if skip and (order < 9 or previous):
                comparedElems = [-1, -1, -1]
                stepsPerFrame = origFrameSpeed
                sortType = oldSortType
                return True
        if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
            sorted = False
            if final:
                if not ignoreErrors:
                    print("Error: number " + str(theArray[comparedElems[0]]) +
                          " is greater than next element " + str(theArray[comparedElems[1]]))
            else:
                break
    if final and not sorted and not ignoreErrors:
        print(theArray)
        exit(0)

    comparedElems = [-1, -1, -1]
    render(True, auxArray)
    stepsPerFrame = origFrameSpeed
    sortType = oldSortType
    return sorted


def render(updateGraphics, auxArray=None, compareInAux=False, addingToHeap=False):
    global frameCounter, frameStart, startTime
    while time.time_ns() - frameStart < 1000000000 / FPS:
        pass
    frameFinish = time.time_ns()
    frameTime = frameFinish - frameStart
    frameStart = frameFinish

    if frameCounter == 100:
        endTime = time.time_ns()
        hundred_elapsed = endTime - startTime
        startTime = endTime
#        if startTime != -1: print("100 frames: " + str(hundred_elapsed))
        frameCounter = 0
    frameCounter += 1

    window.fill(BLACK)
    writeText(sortType, 25, (30, 20))

    for i in range(0, ARRAY_SIZE):
        # if compareInAux or not (i in comparedElems):
        pygame.draw.line(window, intToColor(theArray[i], MAX_INT), \
                         (i + 100, ARRAY_Y_POS - ARRAY_HEIGHT * (theArray[i] / MAX_INT)), (i + 100, ARRAY_Y_POS), 1)
    if not compareInAux:
        for elem in comparedElems:
            if elem > -1 and elem < ARRAY_SIZE:
                pygame.draw.line(window, WHITE, (elem + 100, ARRAY_Y_POS - ARRAY_HEIGHT * (theArray[elem] / MAX_INT)), \
                                 (elem + 100, ARRAY_Y_POS), 2)  # If an element is being compared, draw it in white
            # and a little bit thicker

    # playTone(theArray[comparedElems[0]] + 1, BEEP_DURATION)
    if (auxArray != None): renderAux(auxArray, compareInAux, addingToHeap)
    if updateGraphics: updateAll()


def renderBogo():
    window.fill(BLACK)
    writeText(sortType, 25, (30, 20))
    color = WHITE

    for i in range(0, BOGO_SIZE):
        if not (i in comparedElems):
            color = intToColor(bogoArray[i], MAX_INT)
        else:
            color = WHITE
        pygame.draw.rect(window, color, pygame.Rect(i * (ARRAY_SIZE / BOGO_SIZE) + 100,
                                                    ARRAY_Y_POS - ARRAY_HEIGHT * (bogoArray[i] / MAX_INT),
                                                    ARRAY_SIZE / BOGO_SIZE,
                                                    ARRAY_HEIGHT * (bogoArray[i] / MAX_INT) + 1));
        # pygame.draw.line(window, intToColor(theArray[i], MAX_INT), \
        #           (i + 100, ARRAY_Y_POS - ARRAY_HEIGHT * (theArray[i] / MAX_INT)), (i + 100, ARRAY_Y_POS), 1)
    updateAll()


def renderAux(auxArray, compareInAux, addingToHeap):
    writeText("Auxiliary array", 16, (30, 355))
    ypos = ARRAY_Y_POS + ARRAY_HEIGHT + 30

    for i in range(0, len(auxArray)):
        pygame.draw.line(window, intToColor(auxArray[i], MAX_INT), \
                         (i + 100, ypos - ARRAY_HEIGHT * (auxArray[i] / MAX_INT)), (i + 100, ypos), 1)

    if compareInAux:
        for elem in comparedElems:
            if elem > -1 and elem < ARRAY_SIZE:
                pygame.draw.line(window, WHITE, (elem + 100, ypos - ARRAY_HEIGHT * (auxArray[elem] / MAX_INT)), \
                                 (elem + 100, ypos), 2)

    if addingToHeap:  # Highlight the element in the original array that's being inserted into the heap
        elem = len(auxArray) - 1
        pygame.draw.line(window, WHITE, (elem + 100, ARRAY_Y_POS - ARRAY_HEIGHT * (theArray[elem] / MAX_INT)), \
                         (elem + 100, ARRAY_Y_POS), 2)


def exitCheck():
    global skip, previous
    for thisEvent in pygame.event.get():
        if thisEvent.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        if thisEvent.type == pygame.KEYDOWN:
            if thisEvent.key == pygame.K_RIGHT:
                skip = True
            if thisEvent.key == pygame.K_LEFT:
                skip = True
                previous = True


def insertionSort():
    global sortType, comparedElems, skip, previous, order
    sortType = "Insertion Sort"
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    if checkSorted(0, ARRAY_SIZE, False): return
    unsortedPortionStart = 1
    for i in range(unsortedPortionStart, ARRAY_SIZE):
        renderFrame = random.randint(0, stepsPerFrame - 1)  # Shake things up a bit so that each frame
        # has a more equal chance at being rendered
        comparedElems[0] = unsortedPortionStart
        comparedElems[1] = comparedElems[0] - 1
        while (comparedElems[0] > 0 and theArray[comparedElems[0]] < theArray[comparedElems[1]]):

            if (comparedElems[0] % stepsPerFrame == renderFrame):
                chooseTone([])
                render(True)
                if skip:
                    skip = False
                    if previous:
                        previous = False
                        order -= 1
                    return

            swap(comparedElems[0], comparedElems[1])

            comparedElems[0] -= 1  # Move the index to keep up with the same element
            comparedElems[1] = comparedElems[0] - 1

            exitCheck()

        unsortedPortionStart += 1

    comparedElems = [-1, -1, -1]
    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)

        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 1
    

def doubleSelectionSort():
    global sortType, comparedElems, skip, previous, order
    sortType = "Double Selection Sort"
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    if checkSorted(0, ARRAY_SIZE, False): return
    firstUnsortedElem = 0
    lastUnsortedElem = ARRAY_SIZE - 1

    while firstUnsortedElem <= lastUnsortedElem:
        comparedElems[1] = firstUnsortedElem
        min = comparedElems[1]
        max = comparedElems[1]

        renderFrame = random.randint(0, stepsPerFrame - 1)
        for i in range(firstUnsortedElem, lastUnsortedElem + 1):
            comparedElems[0] = i

            comparedElems[1] = max
            comparedElems[2] = min
            if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
                comparedElems[1] = comparedElems[0]

            if theArray[comparedElems[0]] < theArray[comparedElems[2]]:
                comparedElems[2] = comparedElems[0]

            max = comparedElems[1]
            min = comparedElems[2]

            exitCheck()
            if (comparedElems[0] % stepsPerFrame == renderFrame):
                chooseTone([])
                render(True)
                if skip:
                    skip = False
                    if previous:
                        previous = False
                        order -= 2
                    return

        swap(max, lastUnsortedElem)
        if min == lastUnsortedElem: min = max  # If the last unsorted element just happens to also
        # be the next smallest value, then, per the previous
        # command, it has just swapped places with the max
        # value, so we must update the index accordingly!
        swap(min, firstUnsortedElem)

        firstUnsortedElem += 1
        lastUnsortedElem -= 1

    comparedElems = [-1, -1, -1]
    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)

        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def selectionSort():
    global sortType, comparedElems, skip, previous, order
    sortType = "Selection Sort"
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    if checkSorted(0, ARRAY_SIZE, False): return
    firstUnsortedElem = 0

    while firstUnsortedElem < ARRAY_SIZE:
        comparedElems[2] = firstUnsortedElem
        min = comparedElems[2]

        renderFrame = random.randint(0, stepsPerFrame - 1)
        for i in range(firstUnsortedElem, ARRAY_SIZE):
            comparedElems[0] = i
            comparedElems[2] = min

            if theArray[comparedElems[0]] < theArray[comparedElems[2]]:
                comparedElems[2] = comparedElems[0]

            min = comparedElems[2]

            exitCheck()
            if (comparedElems[0] % stepsPerFrame == renderFrame):
                chooseTone([])
                render(True)
                if skip:
                    if previous:
                        previous = False
                        order -= 2
                    skip = False
                    return

        swap(min, firstUnsortedElem)

        firstUnsortedElem += 1
    comparedElems = [-1, -1, -1]
    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)

        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def merge(subList1, subList2):
    global comparedElems

    # create a combined list
    combinedList = [0] * (subList2[1] - subList1[0])

    combinedListSpot = 0

    comparedElems[0] = subList1[0]
    comparedElems[1] = subList2[0]

    renderFrame = random.randint(0, stepsPerFrame - 1)
    while combinedListSpot < len(combinedList):
        exitCheck()
        if combinedListSpot % stepsPerFrame == renderFrame:
            chooseTone([])
            render(True, combinedList)
            if skip:
                return

        if comparedElems[1] != -1 and \
                (comparedElems[0] == -1 or theArray[comparedElems[0]] > theArray[comparedElems[1]]):
            # If a) the pointer in list 2 hasn't run off the end of the list AND
            # b) either the element pointed to in list 2 is smaller or the pointer
            # in list 1 has run off the end of list 1, then insert the value from list 2
            combinedList[combinedListSpot] = theArray[comparedElems[1]]
            comparedElems[1] += 1
            if comparedElems[1] == subList2[1]:
                comparedElems[1] = -1  # indicates that this pointer has run off the end of its list
        else:
            combinedList[combinedListSpot] = theArray[comparedElems[0]]
            comparedElems[0] += 1
            if comparedElems[0] == subList1[1]:
                comparedElems[0] = -1  # indicates that this pointer has run off the end of its list

        combinedListSpot += 1
    render(True, combinedList)
    comparedElems = [-1, -1, -1]

    renderFrame = random.randint(0, stepsPerFrame - 1)
    for i in range(len(combinedList)):
        exitCheck()
        theArray[subList1[0] + i] = combinedList[i]
        if i % stepsPerFrame == renderFrame:
            chooseTone([theArray[subList1[0] + i]])
            render(True, combinedList)
            if skip:
                return


def mergeSort():
    global sortType, stepsPerFrame, comparedElems, skip, previous, order
    sortType = "Merge Sort"
    render(True)
    stepsPerFrame = int(SPF_DEFAULT / 6)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    mergeSortSublist(0, ARRAY_SIZE)

    stepsPerFrame = SPF_DEFAULT
    if skip:
        if previous:
            previous = False
            order -= 2
        skip = False
        return

    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)

        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def mergeSortSublist(beginIndex, endIndex):
    if endIndex == beginIndex + 1: return
    if checkSorted(beginIndex, endIndex, False, False, True): return

    if skip:
        return

    midpoint = int((beginIndex + endIndex) / 2)
    mergeSortSublist(beginIndex, midpoint)
    mergeSortSublist(midpoint, endIndex)

    merge((beginIndex, midpoint), (midpoint, endIndex))
    render(True, [])


def bubbleSortSublist(startInd, endInd):
    global skip
    firstSortedElem = endInd + 1

    comparedElems[0] = startInd
    comparedElems[1] = startInd + 1
    done = False
    while done == False and firstSortedElem > startInd:
        done = True
        renderFrame = random.randint(0, stepsPerFrame - 1)
        for comparedElems[0] in range(firstSortedElem - 1):
            comparedElems[1] = comparedElems[0] + 1
            exitCheck()
            if comparedElems[0] % stepsPerFrame == renderFrame:
                chooseTone([])
                render(True)
                if skip:
                    return

            if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
                swap(comparedElems[0], comparedElems[1])
                done = False
        firstSortedElem -= 1


def bubbleSort():
    global comparedElems, sortType, skip, previous, order
    sortType = "Bubble Sort"
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    bubbleSortSublist(0, ARRAY_SIZE - 1)

    if skip:
        if previous:
            previous = False
            order -= 2
        skip = False
        return

    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)
        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def shakerSort():
    global comparedElems, sortType, skip, previous, order
    sortType = "Shaker Sort"
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()
    endOfUnsortedPart = ARRAY_SIZE
    startOfUnsortedPart = 0

    comparedElems[0] = 0
    comparedElems[1] = 1
    done = False
    direction = -1
    while done == False and endOfUnsortedPart > startOfUnsortedPart:
        direction *= -1
        done = True
        renderFrame = random.randint(0, stepsPerFrame - 1)
        while startOfUnsortedPart <= comparedElems[0] and \
                comparedElems[0] <= endOfUnsortedPart - 2:
            exitCheck()
            if comparedElems[0] % stepsPerFrame == renderFrame:
                chooseTone([])
                render(True)
                if skip:
                    if previous:
                        previous = False
                        order -= 2
                    skip = False
                    return

            if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
                swap(comparedElems[0], comparedElems[1])
                done = False
            comparedElems[0] += direction
            comparedElems[1] = comparedElems[0] + 1

        if (direction == 1):
            endOfUnsortedPart -= 1
            comparedElems[0] -= 2
            comparedElems[1] -= 2
        else:
            startOfUnsortedPart += 1
            comparedElems[0] += 2
            comparedElems[1] += 2

    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)
        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def getPivotRandomly(beginInd, endInd):
    global PRNGIndex

    randNum = PRNG[PRNGIndex] # Choose from a selection of arbitrary
    # numbers between 0 and 1
    
    PRNGIndex += 1
    if PRNGIndex == len(PRNG): PRNGIndex = 0
    
    offset = int((endInd - beginInd) * randNum) # Will never go out of bounds
    # because we're rounding down
    
    return beginInd + offset

def getPivotBothWays(beginInd, endInd):
    global PRNGIndex, comparedElems

    randNum = PRNG[PRNGIndex] # Choose from a selection of arbitrary
    # numbers between 0 and 1
    
    PRNGIndex += 1
    if PRNGIndex == len(PRNG): PRNGIndex = 0
    
    offset = int((endInd - beginInd) * randNum) # Will never go out of bounds
    # because we're rounding down
    candidate1 = beginInd + offset

    if candidate1 == endInd - 1:
        candidate2 = candidate1 - 1
        candidate3 = candidate1 - 2
    elif candidate1 == beginInd:
        candidate2 = candidate1 + 1
        candidate3 = candidate1 + 2
    else:
        candidate2 = candidate1 + 1
        candidate3 = candidate1 - 1

    renderFrame = random.randint(0, stepsPerFrame - 1)
    
    comparedElems[0] = candidate1
    comparedElems[1] = candidate2

    if renderFrame == 0:
        chooseTone([])
        render(True)

    if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
        bigger = comparedElems[0]
        smaller = comparedElems[1]
    else:
        bigger = comparedElems[1]
        smaller = comparedElems[0]

    comparedElems[1] = bigger
    comparedElems[2] = candidate3
    comparedElems[0] = -1

    if renderFrame == 1:
        chooseTone([])
        render(True)
    if theArray[comparedElems[2]] > theArray[comparedElems[1]]:
        return comparedElems[1]

    comparedElems[1] = smaller

    if renderFrame == 2:
        chooseTone([])
        render(True)
    if theArray[comparedElems[2]] > theArray[comparedElems[1]]:
        return comparedElems[2]

    return comparedElems[1]
    

def getPivotMO3(beginInd, endInd):
    global comparedElems
    "Get pivot by taking the median of the first, last, and middle elements"

 #   renderFrame = random.randint(0, stepsPerFrame - 1)
    midpoint = int((beginInd + endInd) / 2)
    comparedElems[0] = beginInd
    comparedElems[1] = midpoint

    if renderFrame == 0:
        chooseTone([])
        render(True)

    if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
        bigger = comparedElems[0]
        smaller = comparedElems[1]
    else:
        bigger = comparedElems[1]
        smaller = comparedElems[0]

    comparedElems[1] = bigger
    comparedElems[2] = endInd - 1
    comparedElems[0] = -1

    if renderFrame == 1:
        chooseTone([])
        render(True)
    if theArray[comparedElems[2]] > theArray[comparedElems[1]]:
        return comparedElems[1]

    comparedElems[1] = smaller

    if renderFrame == 2:
        chooseTone([])
        render(True)
    if theArray[comparedElems[2]] > theArray[comparedElems[1]]:
        return comparedElems[2]

    return comparedElems[1]


def QuicksortSublist(beginInd, endInd):
    global comparedElems
    renderFrame = random.randint(0, stepsPerFrame - 1)

    if endInd - beginInd > 2:
        pivotInd = getPivotBothWays(beginInd, endInd)
        comparedElems = [-1, -1, -1]

    elif endInd - beginInd == 2:
        comparedElems[0] = beginInd
        comparedElems[1] = beginInd + 1
        if renderFrame == 0:
            chooseTone([])
            render(True)
        if theArray[comparedElems[0]] > theArray[comparedElems[1]]:
            swap(comparedElems[0], comparedElems[1])

        comparedElems = [-1, -1, -1]
        return

    else:
        return

    if checkSorted(beginInd, endInd, False): return

    pivotVal = theArray[pivotInd]

    swap(beginInd, pivotInd)

    comparedElems[0] = beginInd + 1
    comparedElems[2] = endInd - 1
    comparedElems[1] = beginInd  # The pivot is now here; comparedElems[1] will store the pivot
    lowerOutOfPlace = False
    upperOutOfPlace = False
    frame = 0

    while comparedElems[2] >= comparedElems[0]:
        exitCheck()
        if frame % stepsPerFrame == renderFrame:
            chooseTone([])
            render(True)
            if skip:
                return

        if not lowerOutOfPlace and theArray[comparedElems[0]] > theArray[comparedElems[1]]:
            lowerOutOfPlace = True
        if not upperOutOfPlace and theArray[comparedElems[2]] <= theArray[comparedElems[1]]:
            upperOutOfPlace = True

        if lowerOutOfPlace and upperOutOfPlace:
            swap(comparedElems[0], comparedElems[2])
            lowerOutOfPlace = False
            upperOutOfPlace = False

        if not upperOutOfPlace:
            comparedElems[2] -= 1
        if not lowerOutOfPlace:
            comparedElems[0] += 1

        frame += 1

    swap(comparedElems[1], comparedElems[2])
    splitInd = comparedElems[2]  # Now the pivot is stored in comparedElems[2]
    comparedElems = [-1, -1, -1]

    render(True)
    QuicksortSublist(beginInd, splitInd)
    QuicksortSublist(splitInd, endInd)


def Quicksort():
    global comparedElems, sortType, stepsPerFrame, skip, previous, order
    sortType = "Quicksort"
    stepsPerFrame = int(SPF_DEFAULT / 6)
    render(True)
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    QuicksortSublist(0, ARRAY_SIZE)

    stepsPerFrame = SPF_DEFAULT
    if skip:
        if previous:
            previous = False
            order -= 2
        skip = False
        return

    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)
        totalTime = time.time() - beginTime
       # print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2


def heapSort():
    global sortType, skip, comparedElems, theArray, previous, order
    sortType = "Heap Sort"
    render(True)

    activeSleep(1)
    if checkSorted(0, ARRAY_SIZE, False): return
    
    heap = Heap(theArray)

    if skip:
        if previous:
            previous = False
            order -= 2
        skip = False
        return

    heap.addingStage = False

    mainArrInd = 0
    while heap.size() > 0:
        theArray[mainArrInd] = heap.popTop()
        if skip:
            if previous:
                previous = False
                order -= 2
            skip = False
            return
        mainArrInd += 1

    checkSorted(0, ARRAY_SIZE, True)
    comparedElems = [-1, -1, -1]
    if not skip:
        render(True)
        activeSleep(2)
    elif previous:
        order -= 2


def destroy():
    global FPS
    
    flash = False
    exploding = False
    expansionRate = 400
    explosionSize = 200

    i = 3
    shortCycle = False
    cycleCount = 0

    while not flash:
        exitCheck()
    #    time.sleep(0.125)
        render(False)
        FPS = 7.5
        i += 1
        if shortCycle and i == 3:
            i = 0
            shortCycle = False
            cycleCount += 1
        if i == 4:
            i = 0
            shortCycle = True
            if cycleCount == 2: flash = True
            cycleCount += 1
        window.blit(bombFrames[i], bombRect)

        pygame.display.update()

    i = 0
    soundPlaying = False

    FPS = 30
    while True:
        exitCheck()

        render(False)
        window.blit(bombFlashFrames[i], bombRect)
        i += 1
        if i == 12:
            i = 0
        if i > 7: exploding = True
        if exploding:
            if not soundPlaying:
                explodeSound.play()
                soundPlaying = True
            drawExplosion(explosionSize)
            explosionSize += expansionRate
            expansionRate *= 0.9
            if explosionSize > 3200:
                pygame.quit()
                exit(0)

        pygame.display.update()


def swapBogo(index1, index2):
    placeholder = bogoArray[index1]
    bogoArray[index1] = bogoArray[index2]
    bogoArray[index2] = placeholder


def shuffleBogo():
    global skip
    exitCheck()
    renderFrame = random.randint(0, stepsPerFrame - 1)
    for i in range(BOGO_SIZE):
        swapIndex = random.randint(0, BOGO_SIZE - 1)

        if i % stepsPerFrame == renderFrame:
            if random.randint(0, 1) == 0:
                playTone(bogoArray[swapIndex] + 1, BEEP_DURATION)
            else:
                playTone(bogoArray[i] + 1, BEEP_DURATION)
            renderBogo()
            if skip:
                return
        swapBogo(i, random.randint(0, BOGO_SIZE - 1))


def checkBogo():
    global comparedElems, skip
    renderFrame = random.randint(0, stepsPerFrame - 1)
    for i in range(BOGO_SIZE - 1):
        comparedElems[0] = i
        comparedElems[1] = i + 1
        if i % stepsPerFrame == renderFrame:
            chooseTone([])
            renderBogo()
        if bogoArray[comparedElems[0]] > bogoArray[comparedElems[1]]:
            return False
    return True


def initBogo():
    global skip
    renderFrame = random.randint(0, stepsPerFrame - 1)
    for i in range(BOGO_SIZE):
        val = random.randint(0, MAX_INT)
        if i % stepsPerFrame == renderFrame:
            playTone(val + 1, BEEP_DURATION)
            renderBogo()
        bogoArray[i] = val
    skip = False


def bogoSort():
    global comparedElems, sortType, stepsPerFrame, theArray, skip, previous, order
    comparedElems = [-1, -1, -1]
    sortType = "Bogo Sort"
    renderBogo()
    activeSleep(1)
    #    print(sortType)
    beginTime = time.time()

    while not checkBogo():
        if skip:
            if previous:
                previous = False
                order -= 2
            skip = False
            theArray = [0] * ARRAY_SIZE
            return
        shuffleBogo()

    comparedElems = [-1, -1, -1]
    if not skip:
        renderBogo()
        totalTime = time.time() - beginTime
        #    print(totalTime)
        activeSleep(2)
    elif previous:
        order -= 2
    theArray = [0] * ARRAY_SIZE


def quantumBogoSort():
    global comparedElems, sortType, stepsPerFrame, skip, previous, order
    sortType = "Quantum Bogo Sort"
    render(True)
    activeSleep(1)
    if checkSorted(0, ARRAY_SIZE, True, True):
        comparedElems = [-1, -1, -1]
        if not skip:
            render(True)
            activeSleep(2)
        else:
            skip = False
            if previous:
                previous = False
                order -= 2
        return
    sortType = "not sorted :("
    render(True)
    activeSleep(2)
    exitCheck()
    if skip and previous:
        skip = False
        previous = False
        order -= 2
        return
    destroy()


def beginningScreen():
    global skip
    writeText("Basic Sorting Algorithms", 30, (200, 200))
    writeText("(sorting speeds are not to scale with each other)", 20, (132, 250))
    writeText("Press the right arrow key at any time to skip to the next algorithm", 20, (32, 350))
    writeText("Press the right arrow key now", 20, (245, 380))
    updateAll()
    while not skip:
        exitCheck()



sortTypes = [insertionSort, selectionSort, doubleSelectionSort, mergeSort, bubbleSort, \
             shakerSort, Quicksort, heapSort, bogoSort, quantumBogoSort]

beginningScreen()
while order != len(sortTypes):
    if order == 8:
        initBogo()
    else:
        resetArray()
        
    sortTypes[order]()
    #Quicksort()

    order += 1

pygame.quit() # In practice, this statement is completely unreachable
