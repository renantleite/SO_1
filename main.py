import json
from multiprocessing import Barrier, Queue, Semaphore, shared_memory
import Server
import Client

#iniciar somente com 4 ou mais processos
while True:
    try:
        n_processes = int(input("Insira o número de jogadores (mínimo 4): "))
        if n_processes < 4:
            print("Número de jogadores deve ser no mínimo 4. Tente novamente.")
        else:
            break
    except ValueError:
        print("Por favor, insira um número válido.")

b = Barrier(n_processes + 1)  # o +1 é para o servidor

sem = Semaphore(1)

if __name__ == '__main__':
    
    shm = shared_memory.SharedMemory(create=True, size=10)
    data = []

    clients = []
    answerQueue = Queue(n_processes)

    #pegando as perguntas do arquivo Json
    with open('jsonPerguntas.json') as json_file:
        data = json.load(json_file)

    # Iniciar os processos clientes
    for i in range(n_processes):
        c = Client.Client(id=i, questionsJson=data, shm=shm, answerQueue=answerQueue, barrier=b, sem=sem)
        c.start()
        print(f"Cliente {i} iniciado com PID: {c.pid}")  # Imprime o PID do cliente para identificar cada processo
        clients.append(c)

    # Iniciando o servidor
    server = Server.Server(id=1, questionsJson=data, shm=shm, answerQueue=answerQueue, barrier=b, sem=sem)
    server.start()

    # Esperandos todos os clientes finalizarem
    for client in clients:
        client.join() 

    # Finalizando o servidor após os clientes terminarem
    server.join()