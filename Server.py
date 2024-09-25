from multiprocessing import Process, Queue
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.synchronize import Barrier, Semaphore
import time

class Server(Process):
#configurações de tempo para espera e preparação entre perguntas

    tempoAguardandoResposta = 10  
    tempoDePreparacao = 1  

#inicializando as variaveis do servidor    
    def __init__(self, id, questionsJson, shm: SharedMemory, answerQueue: Queue, barrier: Barrier, sem: Semaphore):
        Process.__init__(self)
        self.id = id
        self.questionIndex = None #indice da questão no arquivo Json
        self.correctAnswerIndex = None #indice da resposta da questão no arquivo Json
        self.possibleQuestions = questionsJson #coloca as questões sendo apenas as do arquivo Json
        self.shm = shm #essa é a memoria compartilhada para enviar as perguntas
        self.answerQueue = answerQueue #fila de respostas 
        self.barrier = barrier #barreira para sincronizar as perguntas do servidor aos clientes
        self.sem = sem #semaforo criado para controlar o acesso a memoria compartilhada para evitar condições de corrida
        self.currentQuestionIndex = 0  #indice da pergunta atual
        self.pontuacoes = {} #dicionario para armazenar as pontuações de cada processo

#função para exibir as perguntas no terminal
    def log(self, message):
        print(message, flush=True)
        
#gera a próxima pergunta para ser enviada aos clientes
    def gerarPergunta(self):
        if self.currentQuestionIndex < len(self.possibleQuestions):
            question = self.possibleQuestions[self.currentQuestionIndex]
            self.questionIndex = question['id']
            self.correctAnswerIndex = question['correctAnswerIndex']
        
            
            binaryQuestion = self.questionIndex.to_bytes(2, byteorder='big') # Envia a pergunta através da memória compartilhada            
            self.shm.buf[:2] = binaryQuestion #escreve o valor da pergunta atual na memória compartilhada para que todos os clientes possam acessar            
            self.log('Pergunta: ' + question['question']) #apenas mostra a pergunta no terminal
            
            # Barreira para que todos os clientes estejam prontos para receber a pergunta
            try:
                self.barrier.wait() 
            except Exception as e:
                self.log(f"Erro na barreira: {e}")            
            self.currentQuestionIndex += 1  # Incrementa para a próxima pergunta apenas quando todos os processos chegaram na barreira
        else:
            self.log('Todas as perguntas foram feitas.')
            
#essa função faz a incrementação da pontuação aos clientes se acertar ganha 10 pontos 	
    def pontuar(self, process_id):
        if process_id not in self.pontuacoes:
            self.pontuacoes[process_id] = 10
        else:
            self.pontuacoes[process_id] += 10
            
#essa função serve para printar a pontuação vamos usar no final para mostrar a pontuação e saber quem venceu o jogo 
    def printPontuacao(self):
	    # Imprime a pontuação final de cada cliente
	    print("\nPontuação Final:")
	    for chave, valor in self.pontuacoes.items():
	        print(f'Cliente {chave}: {valor} pontos')
	
	    # Identifica a pontuação máxima
	    max_pontuacao = max(self.pontuacoes.values()) if self.pontuacoes else 0
	
	    # Encontra todos os clientes que têm a pontuação máxima
	    vencedores = [cliente for cliente, pontos in self.pontuacoes.items() if pontos == max_pontuacao]
	
	    # Verifica se há mais de um cliente com a pontuação máxima
	    if len(vencedores) > 1:
	        print(f"\nEmpate! Os clientes com pontuação máxima de {max_pontuacao} pontos são: {', '.join(map(str, vencedores))}")
	    else:
	        print(f"\nVencedor! Cliente {vencedores[0]} com {max_pontuacao} pontos")            
#essa função serve para checar se a resposta está certa ou errada    
    def checkAnswer(self):
        #espera todas as respostas chegarem dentro do tempo limite
        start_time = time.time()
        respostas_recebidas = []
        #enquanto o tempo limite de resposta "10" ainda estiver durando
        while time.time() - start_time < self.tempoAguardandoResposta:
        #enquanto a fila de respostas nao estiver vazia:
            while not self.answerQueue.empty():
            #vai adicionando a fila de respostas para conferir as respostas em ordem de chegada
                resposta = self.answerQueue.get()
                respostas_recebidas.append(resposta)
            time.sleep(0.1)

        self.log('O Tempo Acabou, checando respostas...')

        # Verifica se alguma resposta está correta
        for resposta in respostas_recebidas:
            if resposta['answer'] == self.correctAnswerIndex:
                processId = resposta['id']
                self.log(f'Client {processId} acertou a resposta')
                self.pontuar(processId)
                #esse return True abaixo serve para sair da função quando a primeira resposta certa é encontrada para pontuar apenas o primeiro
                return True

        self.log('Nenhum processo acertou a resposta')
        return False

    def run(self):
        num_perg = 3  
        for _ in range(num_perg):
            self.gerarPergunta()
            self.log('Esperando respostas...')
            self.checkAnswer()
            time.sleep(self.tempoDePreparacao)  
        
        
        self.printPontuacao()