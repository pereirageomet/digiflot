# Event-Driven Architecture

For handling user inputs, but also for breaking static coupling an Event-Driven Architecture (EDA) is implemented as part of the Lab Assistant Software.  
  
There are four categories of events in the Lab Assitant Software:  
1. Events that are emitted after user input, and processed by the corresponding view object

These events trigger the immediate execution of the user input (e.g. a click of a button), and are processed within the corresponding view object. Effectively, these events are direct method calls.  

2. Events that are emitted after user input, and processed by the controller object

These events trigger the immediate execution of the user input (e.g. a click of a button), but causes a cascade of method calls within the whole software. Consequently, the event triggers a method of an object at the top of the class hierarchy, the controller, thereby breaking the static class hierarchy.  

3. Events that are emitted during execution, and processed by the corresponding object 

These events are triggered by the software itself. The sole objects emitting those events are the timer objects of the controller. By using inversion of control, the timer objects can enforce the execution of timed method calls, such as fetching up-to-date sensor data at a given time.  

4. One event that is emitted during execution, and processed by the controller object

The taskModel object emits "statusHasChanged" every time its attribute "status" has changed, e.g. from "PAUSED" to "RUNNING". This is necessary for syncing the countdown of the runtimer object of the controller with the status of the taskModel.  

Every event of category (2) or (4) is registered beforehand by help of the eventManager module.  

**UML diagram**  
All events occuring in the Lab Assistant software are visualized in the following UML:
![events](docs/events.png)