
/* Service holds functions to call the server */
var Service = {
    /* Get the window URL */
    origin: window.location.origin,

    /* Call for python data from the server */
    sendFormData: (data) => {
        var url = this.origin + '/python';
        var promise = fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }).then(response => {
            if(!response.ok) { return response.text().then(text => { throw new Error(text) }); }
            return response.json();
        }).then(res => {
            return res;
        });
        return promise;
    }
}

/* Handles the input view JS */
class InputView {
    constructor() {
        this.input_view = document.querySelector("#input-view");
        this.email_form      =  this.input_view.querySelector("#email-form");
        this.email_input     =  this.input_view.querySelector("#email-input");
        this.substrate_input =  this.input_view.querySelector("#substrate-input");
        this.organism_input  =  this.input_view.querySelector("#organism-input");
        this.submit_button   =  this.input_view.querySelector("#submit-button");
        this.output          =  document.querySelector("#output");

        this.email_form.addEventListener('submit', (event) => {
            event.preventDefault();

            let form_data = {
                email: this.email_input.value,
                args: [this.substrate_input.value, this.organism_input.value]
            }

            /* Reset values */
            this.substrate_input.value = "";
            this.organism_input.value = "";

            /* Reset the URL to not show post parameters */
            window.history.replaceState({}, document.title, "/");

            /* Send the request */
            Service.sendFormData(form_data).then(res => {
                //this.output.innerHTML = res;
                
                console.log(res);
            }).catch(error => {console.log(error); /*this.output.innerHTML = error*/});

        });
    }

    /* Validate the input before sending it to the server */
    checkInput(email_input, substrate_input, organism_input) {
        const emailValidaRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        let error = this.input_view.querySelector("#input_error");
        error.textContent = ""
        error.style.color = ""
        
        substrate_input.style.borderColor = "";
        email_input.style.borderColor = "";
        organism_input.style.borderColor = "";

        if(substrate_input.value.trim() != "" && email_input.value.trim() != "" && emailValidaRegex.test(email_input.value)) {return true;}

        if(email_input.value.trim() == "" || !emailValidaRegex.test(email_input.value)) {
            email_input.style.borderColor = "red";
            error.textContent += "Please enter a valid email!"
            error.style.color = "red"
        }
         
        if(substrate_input.value.trim() == "") {
            substrate_input.style.borderColor = "red";
            error.textContent += "Please enter a substrate!"
            error.style.color = "red"
        }

        return false;
    }
}


/* Run function main on load */
window.addEventListener('load', main);

/* Main function for app.js */
function main() {
    
    /* Initialise the input view */
    let inputView = new InputView();

    /* Routing for different "pages" */
    function renderRoute() {
        /*let page = window.location.hash;*/
        let pageS = window.location.href; 
        let sb = document.getElementById("submit-button");

        switch(pageS){
            case(pageS = "https://transporterpalweb.azurewebsites.net/"):
                    sb.addEventListener('click', function(){
                    document.location.href = "https://transporterpal.com/signoff.html"; 
                }); 
            break;
        }
    }

    /* Call render route and add it to window popstate */
    renderRoute();
    window.addEventListener('popstate', renderRoute);

}