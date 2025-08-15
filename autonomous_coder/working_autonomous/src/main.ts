// Modern TypeScript 5.5 with strict mode
import './style.css'

interface Todo {
  id: string
  text: string
  completed: boolean
  createdAt: Date
}

class TodoApp {
  private todos: Todo[] = []
  private container: HTMLElement
  
  constructor(container: HTMLElement) {
    this.container = container
    this.render()
  }
  
  private addTodo(text: string): void {
    const todo: Todo = {
      id: crypto.randomUUID(),
      text,
      completed: false,
      createdAt: new Date()
    }
    this.todos.push(todo)
    this.render()
  }
  
  private render(): void {
    this.container.innerHTML = `
      <h1>Modern TODO App (2025)</h1>
      <p>Built with Vite 7.1.1 + TypeScript 5.5.4</p>
      <form id="todo-form">
        <input type="text" placeholder="Add a todo..." required />
        <button type="submit">Add</button>
      </form>
      <ul>
        ${this.todos.map(todo => `
          <li class="${todo.completed ? 'completed' : ''}">
            ${todo.text}
          </li>
        `).join('')}
      </ul>
    `
    
    // Add event listeners
    const form = this.container.querySelector('#todo-form') as HTMLFormElement
    form?.addEventListener('submit', (e) => {
      e.preventDefault()
      const input = form.querySelector('input') as HTMLInputElement
      if (input.value.trim()) {
        this.addTodo(input.value.trim())
        input.value = ''
      }
    })
  }
}

// Initialize app
const app = document.querySelector<HTMLDivElement>('#app')!
new TodoApp(app)
