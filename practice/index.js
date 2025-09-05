// console.log(`hello`);
// console.log('i like pizza')
// window.alert('this is an alert!')

// document.getElementById("myH1").textContent = "Hello";
// document.getElementById("myP").textContent = 'I like pizza';

// let age = 25;
// let price = 10.99;
// let gpa = 2.1;

// console.log(`You are ${age} years old and the price is $${price}`);
// console.log(typeof age);

// let firstName = "chuyo";
// console.log(typeof firstname);
// //let isStudent = true;
// // console.log(`enrolled: ${isStudent}`);

// let fullname = "biggie";
// let age = "20";
// let student = true;

// document.getElementById("p1").textContent = `your name is ${fullname}`;
// document.getElementById("p2").textContent = age;
// document.getElementById("p3").textContent = student;

// let username;
// //username = window.prompt("what's your username?");
// console.log(username); console.log(`your name is ${firstName}`);
// let email = "bro@gmail.com";
// console.log(`your email is ${email}`)

// let online = false;
// console.log(`bro is online: ${online}`);
// let forSale = true;

// console.log(`is this car for sale: ${forSale}`)
let username;

document.getElementById("mySubmit").onclick = function(){
    username = document.getElementById("myText").value;
    document.getElementById("myh1").textContent = `Hello ${username}`;
    console.log(username);

}

let x= "pizza";
let y = "pizza";
let z= "pizza"
x = Number(x);
y = String(y);
z = Boolean(z);

let radius;
let circumference;

let pi = 3.14159;
radius = window.prompt('enter the radius of a circle');
radius = Number(radius);
circumference = 2*pi*radius;
console.log(circumference);

