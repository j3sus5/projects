const display = document.getElementById("display");

function appendToDisplay(input){
    const operators = ["*", "-", "+","/","%"];
    
    if(display.textContent === "0"){
        if(operators.includes(input)){
            display.textContent += input;
        }
        else{
            display.textContent = input;
        }
    }
    else{
        display.textContent += input;
    }
}
function clearDisplay(){
    display.textContent = "0";
}
function calculate(){
    try{
        const answer = display.textContent;
        const result = eval(answer);
        display.textContent = result;
    }
    catch(error){
        display.textContent = "Error";
    }
}
function deleteOne(){
    display.textContent = display.textContent.slice(0, -1) || 0;
}
document.addEventListener("keydown", (e) => {
    if (e.key >= "0" && e.key <= "9") {
        appendToDisplay(e.key);
    }
    else if (e.key === ".") {
        appendToDisplay(".");
    }
    else if (["+", "-", "*", "/"].includes(e.key)) {
        appendToDisplay(e.key);
    }
    else if (e.key === "Enter" || e.key === "=") {
        e.preventDefault();
        calculate();
    }
    else if (e.key === "Backspace") {
        e.preventDefault();
        deleteOne();
    }
    else if(e.key === "Delete") {
        clearDisplay();
    }
});

