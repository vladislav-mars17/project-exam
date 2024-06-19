function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
 return cookieValue;
}

function getAllTodos(url) {
  fetch(url, {
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    }
  })
  .then(response => response.json())
  .then(data => {

    const list_question = document.getElementById("list_question");
    list_question.innerHTML = "";
    
    const question_id = document.getElementById("question_id");
    question_id.innerHTML = "";

    const list_answer = document.getElementById("list_answer");
    list_answer.innerHTML = "";
    
    const several_answers = document.getElementById("several_answers");
    several_answers.innerHTML = "";

    if ((data.list_question).length == 0) {
      window.location.href = '/table/'
    } else {
      (data.list_question).forEach(question => {
        const questionHTMLElement = `<p>${question.text}</p>`
        list_question.innerHTML += questionHTMLElement;

        const questionIDHTMLElement = `<p>${question.id}</p>`
        question_id.innerHTML += questionIDHTMLElement;
      });
      
      let number_correct_answers = 0;

      for (let i=0; i<(data.list_answers).length; i++) {
        if ((data.list_answers)[i].correct == true) {
          number_correct_answers = number_correct_answers + 1;
        }
      }

      let input_type = 'radio'

      if (number_correct_answers > 1) {
        input_type = 'checkbox'
        several_answers.innerHTML = `<p>Выберите несколько вариантов ответа</p>`
      }

      for (let i=0; i<(data.list_answers).length; i++) {
        const answerHTMLElement = `
          <div class="mb-3 form-check">
            <input type="${input_type}" class="form-check-input" id="${i}" name="${(data.list_answers)[i].question_id}" value="${(data.list_answers)[i].id}">
            <label class="form-check-label" for="${i}">${(data.list_answers)[i].text}</label>
          </div>`
        list_answer.innerHTML += answerHTMLElement;
      }
    }
  });
}

function addTodo(url, payload) {
  fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({payload: payload})
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
  });
}
