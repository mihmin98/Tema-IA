#!/usr/bin/env python3

import sys
import os
import re
import time
import multiprocessing
import psutil
import memory_profiler


class NodParcurgere:
    def __init__(self, info, parinte):
        self.info = info
        self.parinte = parinte

    def obtine_drum(self):
        l = [self]
        nod = self
        while nod.parinte != None:
            l.insert(0, nod.parinte)
            nod = nod.parinte
        return l

    def get_drum_string(self):
        l = self.obtine_drum()
        string = ''
        for nod in l:
            string += str(nod) + ', '
        return string

    def get_solutie_string(self, index=None):
        string = ''
        if index != None:
            string += str(index) + ': '
        string += self.get_drum_string()[:-2]
        string += 3 * '\n' + 10 * '#' + 3 * '\n'

        return string

    def contine_in_drum(self, info_nod):
        nod = self
        while nod is not None:
            if nod.info == info_nod:
                return True
            nod = nod.parinte
        return False

    def get_string(self):
        return self.info

    def __str__(self):
        return self.get_string()

    def __repr__(self):
        return self.get_string()


class Graph():
    def __init__(self, start, lista_cuv):
        self.start = start
        self.lista_cuv = lista_cuv

    def genereaza_succesori(self, nod_curent):
        lista_cuv_succesori = []
        lista_succesori = []

        cuv_curent = nod_curent.info
        for cuv in self.lista_cuv:
            for k in range(2, len(cuv_curent) + 1):
                if cuv_curent != cuv and cuv_curent[-k:] == cuv[:k]:
                    lista_cuv_succesori.append(cuv)

        # cuv_gasite = cate cuvinte care sunt posibili succesori am gasit, daca e 0 atunci cuv_curent e cuv de inchidere
        cuv_gasite = len(lista_cuv_succesori)
        for cuv_succ in lista_cuv_succesori:
            if not nod_curent.contine_in_drum(cuv_succ):
                nod_nou = NodParcurgere(cuv_succ, nod_curent)
                lista_succesori.append(nod_nou)

        return (lista_succesori, cuv_gasite)


# global vars for recursive functions
continua = True
nr_sol_rec = 0
index_solutie = 1


def breadth_first(gr, nr_solutii, output_file):
    output_file = re.sub('.txt', '_bf.txt', output_file)
    f = open(output_file, 'w')

    coada = [NodParcurgere(gr.start, None)]
    continua = True
    index_solutie = 1

    while len(coada) > 0 and continua:
        nod_curent = coada.pop(0)

        succesori, cuv_gasite = gr.genereaza_succesori(nod_curent)
        if cuv_gasite == 0:
            # Solutie
            f.write(nod_curent.get_solutie_string(index_solutie))

            index_solutie += 1
            nr_solutii -= 1
            if nr_solutii == 0:
                continua = False

        coada.extend(succesori)

    f.close()


def depth_first(gr, nr_solutii, output_file):
    global continua, nr_sol_rec, index_solutie
    continua = True
    nr_sol_rec = nr_solutii
    index_solutie = 1

    output_file = re.sub('.txt', '_df.txt', output_file)
    f = open(output_file, 'w')

    df(NodParcurgere(gr.start, None), f)


def df(nod_curent, f):
    global continua, nr_sol_rec, index_solutie

    if not continua:
        return

    succesori, cuv_gasite = gr.genereaza_succesori(nod_curent)
    if cuv_gasite == 0:
        # Solutie
        f.write(nod_curent.get_solutie_string(index_solutie))
        index_solutie += 1
        nr_sol_rec -= 1
        if nr_sol_rec == 0:
            continua = False

    for succ in succesori:
        df(succ, f)


def depth_first_iterative(gr, nr_solutii, adancime_max, output_file):
    global continua, nr_sol_rec, index_solutie
    continua = True
    nr_sol_rec = nr_solutii
    index_solutie = 1

    output_file = re.sub('.txt', '_dfi.txt', output_file)
    f = open(output_file, 'w')

    for i in range(1, adancime_max + 1):
        dfi(NodParcurgere(gr.start, None), i, f)


def dfi(nod_curent, adancime_max_curenta, f):
    global continua, nr_sol_rec, index_solutie

    if adancime_max_curenta <= 0 or not continua:
        return

    adancime_max_curenta -= 1

    succesori, cuv_gasite = gr.genereaza_succesori(nod_curent)
    if cuv_gasite == 0:
        # Solutie
        f.write(nod_curent.get_solutie_string(index_solutie))
        index_solutie += 1
        nr_sol_rec -= 1
        if nr_sol_rec == 0:
            continua = False

    for succ in succesori:
        dfi(succ, adancime_max_curenta, f)


def run(p, polling_rate, intervals):
    t1 = time.time()
    mem_usage = []
    p.start()
    for i in range(intervals):
        if not p.is_alive():
            break
        mem_usage.append(memory_profiler.memory_usage(
            proc=p.pid, interval=polling_rate))

    if p.is_alive():
        p.terminate()
        p.join()
    t2 = time.time()
    diff = t2 - t1
    max_mem = max(mem_usage)[0]

    return (diff, max_mem)


if __name__ == '__main__':
    timeout_value = float(sys.argv[1])
    nr_solutii = int(sys.argv[2])
    input_file = sys.argv[3]
    output_file = re.sub('input', 'output', input_file)

    lista_cuvinte = []
    with open(input_file, 'r') as f:
        first_line = f.readline()
        first_line = re.sub('cuvant start: ', '', first_line)
        lista_cuvinte.append(first_line[:-1])

        for line in f:
            lista_cuvinte.append(line[:-1])
        # dam cu [:-1] ca sa scapam de \n din fiecare cuvant

    gr = Graph(lista_cuvinte[0], lista_cuvinte)

    polling_rate = 0.005  # 5ms polling rate
    intervals = int(timeout_value / polling_rate)

    # Breadth First
    p = multiprocessing.Process(
        target=breadth_first, name='breadth_first', args=(gr, nr_solutii, output_file))

    t, mem = run(p, polling_rate, intervals)

    print('bf:', round(t * 1000), 'ms')
    print(mem, 'MiB\n')

    # Depth First
    p = multiprocessing.Process(
        target=depth_first, name='depth_first', args=(gr, nr_solutii, output_file))

    t, mem = run(p, polling_rate, intervals)

    print('df:', round(t * 1000), 'ms')
    print(mem, 'MiB\n')

    # Depth First Iterative
    p = multiprocessing.Process(
        target=depth_first_iterative, name='depth_first_iterative', args=(gr, nr_solutii, 20, output_file))

    t, mem = run(p, polling_rate, intervals)

    print('dfi:', round(t * 1000), 'ms')
    print(mem, 'MiB\n')
