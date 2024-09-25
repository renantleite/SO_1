from multiprocessing import Process, Queue
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.synchronize import Barrier, Semaphore
import random
import time

class Client(Process):
#configurações de tempo para espera e preparação entre perguntas
    tempoAguardandoResposta = 10  
    tempoDePreparacao = 1  
    
#inicializando as variaveis do client   
    def __init__(self, id, questionsJson, shm: SharedMemory, answerQueue: Queue, barrier: Barrier, sem: Semaphore):
        Process.__init__(self)
        self.id = id
        self.possibleQuestions = questionsJson #questões do Json
        self.shm = shm #memoria compartilhada para receber as perguntas
        self.currentAnswer = None #pergunta atual
        self.answerQueue = answerQueue #fila de respostas dos clientes
        self.barrier = barrier #barreira para sincronizar os clientes ao servidor
        self.semaphore = sem #semaforo para controlar o acesso a memoria compartilhada evitando condições de corrida

#função para exibir as respostas dos clientes no terminal
    def log(self, message):
        print('Client ' + str(self.id) + ': ' + message, flush=True)

#função para clientes responderem a pergunta
    def responderPergunta(self):
        # seleciona a pergunta com base no índice
        question = next((q for q in self.possibleQuestions if q['id'] == self.questionIndex), None)
        # se não tiver pergunta retorna sem resposta
        if question is None:
            return
        optionsLength = len(question['options'])
        #respostas aleatorias por isso o uso do random
        self.currentAnswer = random.randint(0, optionsLength - 1)
        
        # Coloca a resposta na fila de respostas
        self.answerQueue.put({'id': self.id, 'answer': self.currentAnswer})
        #chama a função log para printar a resposta do cliente 
        self.log('Resposta: ' + question['options'][self.currentAnswer])
        
# essa função serve para checar se há uma nova pergunta e se tiver responde ela
    def checarPergunta(self):
        self.semaphore.acquire() #semaforo criada para acessar a memoria compartilhada
        questionIndex = int.from_bytes(self.shm.buf[:2], byteorder='big') # essa linha é feita para ler a pergunta disponivel na memoria compartilhada
        #caso o index da questao seja > 0
        if questionIndex > 0:
        #define o indice da pergunta e logo abaixo chama a função responderPergunta
            self.questionIndex = questionIndex
            self.responderPergunta()
        # logo após é feita a liberação da memoria compartilhada liberando o semaforo
        self.semaphore.release()
        
        # Aguarda que todos os processos estejam prontos e faz a sincronização com o servidor
        try:
            self.barrier.wait()
        except Exception as e:
            self.log(f"Erro na barreira: {e}")
            
#roda a classe client verificando se há perguntas com a função chegarPergunta
    def run(self):
        while True:
            self.checarPergunta()

