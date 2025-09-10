// Main application entry point
import './styles.css';

interface AppState {
  count: number;
  message: string;
}

class App {
  private state: AppState = {
    count: 0,
    message: 'Welcome to your app!'
  };
  
  constructor(private container: HTMLElement) {
    this.render();
    this.attachEventListeners();
  }
  
  private render(): void {
    this.container.innerHTML = `
      <div class="app">
        <h1>${this.state.message}</h1>
        <div class="counter">
          <button id="decrement">-</button>
          <span class="count">${this.state.count}</span>
          <button id="increment">+</button>
        </div>
        <p>Built with TypeScript and Vite</p>
      </div>
    `;
  }
  
  private attachEventListeners(): void {
    this.container.querySelector('#increment')?.addEventListener('click', () => {
      this.state.count++;
      this.render();
      this.attachEventListeners();
    });
    
    this.container.querySelector('#decrement')?.addEventListener('click', () => {
      this.state.count--;
      this.render();
      this.attachEventListeners();
    });
  }
}

// Initialize app
const appElement = document.querySelector<HTMLDivElement>('#app');
if (appElement) {
  new App(appElement);
}
