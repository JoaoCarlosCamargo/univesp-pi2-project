// Função para ler o texto
function lerTexto(texto) {
//    console.log("Função lerTexto foi chamada");  // Log de depuração
    const speech = new SpeechSynthesisUtterance(texto);
    speech.lang = 'pt-BR';  // Define o idioma como português do Brasil
    speech.rate = 1;        // Velocidade da fala (1 é o valor padrão)
    speech.pitch = 1;       // Tom da fala (1 é o valor padrão)

    // Inicia a síntese de voz
//    console.log("Iniciando a leitura do texto: ", texto);  // Log de depuração com o texto a ser lido
    window.speechSynthesis.speak(speech);
}

// Adiciona evento ao botão para ler o texto
document.getElementById('ler-texto-btn').addEventListener('click', function() {
//    console.log("Botão foi clicado");  // Log de depuração

    // Recupera o texto a ser lido
    const conteudo = document.getElementById('conteudo').innerText;
    const texto = document.getElementById('texto-a-ler').innerText;

//    console.log("Texto recuperado: ", conteudo, texto);  // Log de depuração do texto

    // Junta o conteúdo e o texto em uma string
    const textoCompleto = conteudo + ". " + texto;

    // Chama a função para ler o texto
    lerTexto(textoCompleto);
});

// Adiciona evento ao botão para ler o texto
document.getElementById('ler-texto-btn2').addEventListener('click', function() {
//    console.log("Botão foi clicado");  // Log de depuração

    // Recupera o texto a ser lido
    const conteudo = document.getElementById('conteudo2').innerText;
    const texto = document.getElementById('texto-a-ler2').innerText;

//    console.log("Texto recuperado: ", conteudo, texto);  // Log de depuração do texto

    // Junta o conteúdo e o texto em uma string
    const textoCompleto = conteudo + ". " + texto;

    // Chama a função para ler o texto
    lerTexto(textoCompleto);
});

// Adiciona evento ao botão para ler o texto
document.getElementById('ler-texto-btn3').addEventListener('click', function() {
//    console.log("Botão foi clicado");  // Log de depuração

    // Recupera o texto a ser lido
    const conteudo = document.getElementById('conteudo3').innerText;
    const texto = document.getElementById('texto-a-ler3').innerText;

//    console.log("Texto recuperado: ", conteudo, texto);  // Log de depuração do texto

    // Junta o conteúdo e o texto em uma string
    const textoCompleto = conteudo + ". " + texto;

    // Chama a função para ler o texto
    lerTexto(textoCompleto);
});