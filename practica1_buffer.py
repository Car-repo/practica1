#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 10:06:16 2022

@author: alumno
"""
from random import randint
from time import sleep
from multiprocessing import Semaphore,BoundedSemaphore,Array,Value,Process,Manager

def min_positivo(array,N,stack):
    """
    Encuentra el minimo valor positivo, buscando solo en el principio del buffer
    de cada productor, que corresponde a los valores [k*stack]. Devuelve -1 
    si y solo si todos los valores son -1.
    """
    
    minimum, index = array[0], 0
    for j in range(N):
        temp = array[j*stack]
        if minimum < 0 and temp >= 0:
            minimum = temp
            index = j
        elif temp < minimum and temp >= 0:
            minimum = temp   
            index = j
        
    return minimum,index


def consumir(array,pid,stack):
    """
    Cuando el consumidor retire un producto, se mueve la informacion una posicion
    y se guarda un 0 en la que haya quedado vacia.
    """
    
    offset = pid*stack
    for j in range(stack):
        if j == stack-1:
            array[offset+j] = 0   
        else:
            array[offset+j] = array[offset+j+1]


def productor(pid,array,semaforo,lock,position,informacion):
    """
    El productor tiene un buffer de longitud {stack}, que se corresponde con una
    parte del array compartido; una vez que se haya llenado esperara a que se 
    consuma algun valor.
    
    El valor {posicion} recuerda cual es el offset para colocar la proxima
    produccion. El proceso productor lo aumenta, mientras que el consumidor
    lo disminuye.
    """
    
    _,n,stack,_,condition = informacion
    posicion, ultimo = position
    
    nonempty, nonfull = semaforo 
    for j in range(n+1):
        nonfull.acquire()
        lock.acquire()
        indice = pid*stack+posicion.value
        if j == n:
            array[indice] = -1
            print(f"productor/{pid} ha terminado")
        else:
            array[indice] += randint(0,8) + ultimo.value
            ultimo.value = array[indice]
            print(f"turno {j+1}, productor/{pid} ha producido {array[indice]}")
            posicion.value += 1
            if j == 0:
                condition.value += 1
        lock.release()
        nonempty.release()
        sleep(randint(0,3)/10)
    
    
def consumidor(array,semaforos,lock,position,informacion):
    """
    Busca el minimo, si es -1 termina; en caso contrario almacena el valor,
    modifica el buffer de ese productor y ajusta la posicion donde el productor
    guardara el proximo valor.
    """
    
    N,_,stack,resultados,condition = informacion
    
    while condition.value != N:
        pass
    
    loop = True
    while loop:
        #cada vez que consuma, adquiere todos los semaforos
        for par in semaforos:
            nonempty, _ = par
            nonempty.acquire()            
        
        lock.acquire()
        minimum, index = min_positivo(array,N,stack)
        _, nonfull = semaforos[index]
        if minimum == -1:
            print("consumidor termina")
            loop = False
            continue
        print(f"se consume posicion {index*stack}; se guarda valor {minimum}")
        resultados += [minimum]
        consumir(array,index,stack)
        posicion, _ = position[index]
        posicion.value -= 1
        
        #revierte la adquisicion de los semaforos que no se han usado
        for j in (x for x in semaforos if x != semaforos[index]):
            nonempty, _ = j
            nonempty.release()
        lock.release()
        nonfull.release()
            
 
if __name__ == "__main__":
     
    N = 4 #cuantos productores
    turnos = 7 #cuantas veces producen
    stack = 3 #tamaño del almacen
    lp = []
    
    semaforos = [(Semaphore(0),BoundedSemaphore(stack)) for _ in range(N)] # (nonempty, nonfull)
    lock = BoundedSemaphore(1)
    posiciones = [(Value('i',0),Value('i',0)) for j in range(N)] #offset, ultimo_valor_producido
    array = Array('i',N*stack)
    resultados = Manager().list()
    condition = Value('i',0) #cuando valga N se podra consumir productos
    
    informacion = (N,turnos,stack,resultados,condition)
    
    consumidor = Process(target=consumidor, args=(array,semaforos,lock,posiciones,informacion))
    for pid in range(N):
        semaforo = semaforos[pid]
        posicion = posiciones[pid]
        lp += [Process(target=productor, args=(pid,array,semaforo,lock,posicion,informacion))]
    
    for proc in lp:
        proc.start()
    consumidor.start()
    
    for proc in lp:
        proc.join()
    consumidor.join()
    
    print(resultados)

