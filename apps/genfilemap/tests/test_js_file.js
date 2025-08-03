// JavaScript test file to verify file map generation

function greet(name) {
  return `Hello, ${name}!`;
}

document.addEventListener("DOMContentLoaded", function () {
  const greeting = greet("World");
  console.log(greeting);
});

class Counter {
  constructor(initialValue = 0) {
    this.count = initialValue;
  }

  increment() {
    this.count++;
    return this.count;
  }
}
