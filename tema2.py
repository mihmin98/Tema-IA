#!/usr/bin/env python3

import sys
import os
import re
import time
import multiprocessing
import psutil
import memory_profiler


class NodParcurgere:
    def __init__(self, info, stare_incuietoare, parinte, cost):
        self.info = info
        self.stare_incuietoare = stare_incuietoare
        self.parinte = parinte
        self.cost = cost
        self.f = 0
        self.h = 0

    def obtine_drum(self):
        l = [self]
        nod = self
        while nod.parinte != None:
            l.insert(0, nod.parinte)
            nod = nod.parinte
        return l

    def contine_in_drum(self, stare_incuietoare):
        nod = self
        while nod is not None:
            if nod.stare_incuietoare == stare_incuietoare:
                return True
            nod = nod.parinte
        return False

    def get_drum_string(self):
        l = self.obtine_drum()

        string = 'Initial: ' + l[0].get_stare_string()
        for i in range(0, len(l) - 1):
            string += '\n' + str(i+1) + ') Incuietori: ' + \
                l[i].get_stare_string() + '.'
            string += '\nFolosim cheia: ' + \
                l[i+1].get_cheie_string() + ' pentru a ajunge la ' + \
                l[i+1].get_stare_string() + '.'

        string += '\n\nIncuietori(stare scop): ' + \
            l[len(l) - 1].get_stare_string()
        string += '\nS-au realizat ' + str(len(l) - 1) + ' operatii.'

        return string

    def get_solutie_string(self, index=None):
        string = ''
        if index != None:
            string += str(index) + ': '
        string += self.get_drum_string()
        string += 3 * '\n' + 10 * '#' + 3 * '\n'

        return string

    def get_stare_string(self):
        string = '['

        for elem in self.stare_incuietoare:
            string += 'inc('
            if elem == 0:
                string += 'd,0'
            else:
                string += 'i,' + str(elem)
            string += '),'

        string = string[:-1] + ']'
        return string

    def get_cheie_string(self):
        string = '['

        if self.info != None:
            for elem in self.info:
                if elem == -1:
                    string += 'd'
                elif elem == 0:
                    string += 'g'
                else:
                    string += 'i'
                string += ','

        string = string[:-1] + ']'
        return string

    def get_string(self):
        # TODO
        return ''

    def __str__(self):
        return self.get_stare_string()
        # return self.get_string()

    def __repr__(self):
        return self.get_stare_string()
        # return self.get_string()


'''
Incuietoare
val > 0 -> incuiat
0 -> descuiat

Cheie
d = -1
g = 0
i = +1

0 - 1 = 0

heuristica: suma incuietorii sa fie cat mai mica
'''


class Graph:
    def __init__(self, nr_incuietori, lista_chei):
        self.nr_incuietori = nr_incuietori
        self.start = [1] * nr_incuietori
        self.scop = [0] * nr_incuietori
        self.lista_chei = lista_chei
        self.alpha = None

    def genereaza_succesori(self, nod_curent):
        lista_succesori = []

        for i in range(self.nr_incuietori):
            stare_noua = self.descuie(
                nod_curent.stare_incuietoare, self.lista_chei[i])
            if not nod_curent.contine_in_drum(stare_noua):
                nod_nou = NodParcurgere(
                    self.lista_chei[i], stare_noua, nod_curent, nod_curent.cost + 1)
                lista_succesori.append(nod_nou)

        return lista_succesori

    def descuie(self, incuietoare, cheie):
        ret = list(incuietoare)  # Dam cu list() ca sa copiem lista

        for i in range(self.nr_incuietori):
            ret[i] += cheie[i]
            if ret[i] < 0:
                ret[i] = 0

        return ret

    def h(self, stare):
        if self.alpha == None:
            sum_list = []
            for cheie in self.lista_chei:
                s = 0
                for elem in cheie:
                    s += elem
                sum_list.append(s)
            min_val = min(sum_list)
            sum_list = [x+abs(min_val) for x in sum_list]
            self.alpha = sum(sum_list) / len(sum_list)
            print('alpha: ', self.alpha)

        return sum(stare) / self.alpha


def ucs(gr, nr_solutii, output_file):
    output_file = re.sub('.txt', '_ucs.txt', output_file)
    f = open(output_file, 'w')

    coada = [NodParcurgere(None, gr.start, None, 0)]
    continua = True

    while len(coada) > 0 and continua:
        nod_curent = coada.pop(0)

        if nod_curent.stare_incuietoare == gr.scop:
            # Solutie
            f.write(nod_curent.get_solutie_string())
            nr_solutii -= 1
            if nr_solutii == 0:
                continua = False

        succesori = gr.genereaza_succesori(nod_curent)
        for succ in succesori:
            i = 0
            for i in range(len(coada)):
                if coada[i].cost >= succ.cost:
                    break
            coada.insert(i, succ)

    f.close()


def a_star(gr, nr_solutii, output_file):
    open_list = [NodParcurgere(None, gr.start, None, 0)]
    closed_list = []
    continua = True

    output_file = re.sub('.txt', '_a_star.txt', output_file)
    f = open(output_file, 'w')

    while len(open_list) > 0 and continua:
        nod_curent = open_list.pop(0)
        closed_list.append(nod_curent)

        if nod_curent.stare_incuietoare == gr.scop:
            f.write(nod_curent.get_solutie_string())
            nr_solutii -= 1
            if nr_solutii == 0:
                continua = False

        succesori = gr.genereaza_succesori(nod_curent)

        print('succesori:', succesori)
        for succ in succesori:
            succ.h = gr.h(succ.stare_incuietoare)
            succ.f = succ.cost + succ.h

            # Verific daca deja exista starea in lista closed
            x = [nod for nod in closed_list if succ.stare_incuietoare ==
                 nod.stare_incuietoare]
            print('closed x:', x)
            if len(x) > 0:
                x = x[0]
                if succ.f < nod_curent.f:
                    x.parinte = nod_curent
                    x.cost = succ.cost
                    x.f = succ.f

            else:
                # Verific daca deja exista starea in lista open
                x = [nod for nod in open_list if succ.stare_incuietoare ==
                     nod.stare_incuietoare]
                print('open x:', x)
                if len(x) > 0:
                    x = x[0]
                    if succ.cost < x.cost:
                        x.parinte = nod_curent
                        x.cost = succ.cost
                        x.f = f
                else:
                    # Nu e nici in closed nici in open
                    open_list.append(succ)

        open_list.sort(key=lambda x: (x.f, -x.cost))

    f.close()


def a_star_v2(gr, nr_solutii, output_file):
    output_file = re.sub('.txt', '_a_star.txt', output_file)
    f = open(output_file, 'w')

    coada = [NodParcurgere(None, gr.start, None, 0)]
    continua = True

    while len(coada) > 0 and continua:
        nod_curent = coada.pop(0)

        if nod_curent.stare_incuietoare == gr.scop:
            # Solutie
            f.write(nod_curent.get_solutie_string())
            nr_solutii -= 1
            if nr_solutii == 0:
                continua = False

        succesori = gr.genereaza_succesori(nod_curent)
        for succ in succesori:
            succ.h = gr.h(succ.stare_incuietoare)
            succ.f = succ.cost + succ.h
        coada.extend(succesori)

        coada.sort(key=lambda nod: (nod.f, -nod.cost))

    f.close()


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

    lista_chei = []
    with open(input_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            cheie = []
            for char in line:
                if char == 'i':
                    cheie.append(1)
                elif char == 'g':
                    cheie.append(0)
                elif char == 'd':
                    cheie.append(-1)
            lista_chei.append(cheie)

    gr = Graph(len(lista_chei[0]), lista_chei)

    polling_rate = 0.01
    intervals = int(timeout_value / polling_rate)

    # Uniform Cost Search
    p = multiprocessing.Process(
        target=ucs, name='ucs', args=(gr, nr_solutii, output_file))
    t, mem = run(p, polling_rate, intervals)

    print('ucs:', round(t * 1000) / 1000, 's')
    print(mem, 'MiB\n')

    p = multiprocessing.Process(
        target=a_star_v2, name='a_star_v2', args=(gr, nr_solutii, output_file))
    t, mem = run(p, polling_rate, intervals)

    print('a*:', round(t * 1000) / 1000, 's')
    print(mem, 'MiB\n')

    #ucs(gr, nr_solutii, output_file)
    #a_star_v2(gr, nr_solutii, output_file)
