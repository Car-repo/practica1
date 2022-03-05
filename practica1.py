#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 10:06:16 2022

@author: alumno
"""
from random import randint
from multiprocessing import Semaphore,BoundedSemaphore,Array,Value,Process,Manager

def min_positivo(array):
    """
    Encuentra el minimo valor positivo. Devuelve -1 si y solo si todos los valores
    son -1.
    """
    
    minimum, index = array[0], 0
    for j in range(len(array)):
        temp = array[j]
        if minimum < 0 and temp >= 0:
            minimum = temp
            index = j
        elif temp < minimum and temp >= 0:
            minimum = temp   
            index = j
        
    return minimum,index


def productor(pid,array,semaforo,condition,n):
    """
    El productor deposita su producto en una unica casilla y espera a tener
    espacio libre. Señaliza la primera produccion para avisar al consumidor.
    """
    
    nonempty, empty = semaforo 
    for j in range(0,n+1):
        empty.acquire()
        if j == n:
            array[pid] = -1
            print(f"productor/{pid} ha terminado")
        else:
            array[pid] += randint(0,8)
            print(f"turno {j+1}, productor/{pid} ha producido {array[pid]}")
            if j == 0:
                with condition.get_lock():
                    condition.value += 1
        nonempty.release()
    
    
def consumidor(array,semaforos,condition,N,lista):
    """
    El consumidor consume el minimo valor disponible producido por los productores.
    El valor -1 significa que el productor ya termino, por lo que solo se utiliza
    para la parada y no se consume.
    """
    
    while condition.value != N: #espera a que todos produzcan inicialmente
        pass
    
    while True:
        #cada vez que intente consumir, adquiere todos los semaforos
        for par in semaforos:
            nonempty, _ = par
            nonempty.acquire()      
                                     
        minimum, index = min_positivo(array) #busca el minimo
        _, empty = semaforos[index]
        if minimum == -1:
            print("consumidor termina")
            break
        lista += [minimum]
        print(f"se consume posicion {index}; se guarda valor {minimum}")
        
        #revierte la adquisicion de los semaforos que no se han usado
        for j in (x for x in semaforos if x != semaforos[index]):
            nonempty, _ = j
            nonempty.release()    
        empty.release() #el productor tiene capacidad de producir
            
 
if __name__ == "__main__":

    N = 4
    turnos = 7
    semaforos = [(Semaphore(0),BoundedSemaphore(1)) for _ in range(N)] # (nonempty, empty)
    lp = []
    array = Array('i',N)
    resultados = Manager().list()
    condition = Value('i',0)
    
    consumidor = Process(target=consumidor, args=(array,semaforos,condition,N,resultados))
    for pid in range(N):
        semaforo = semaforos[pid]
        lp += [Process(target=productor, args=(pid,array,semaforo,condition,turnos))]
    
    for proc in lp:
        proc.start()
    consumidor.start()
    
    for proc in lp:
        proc.join()
    consumidor.join()
    
    print(resultados)

