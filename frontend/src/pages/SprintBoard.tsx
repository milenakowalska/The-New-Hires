import { useState, useEffect, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import api from '../api/client';
import { Calendar } from 'lucide-react';

interface Ticket {
    id: number;
    title: string;
    description: string;
    status: string;
    priority: string;
    due_date?: string;
}

const columns = {
    'BACKLOG': { id: 'BACKLOG', title: 'Backlog' },
    'TODO': { id: 'TODO', title: 'To Do' },
    'IN_PROGRESS': { id: 'IN_PROGRESS', title: 'In Progress' },
    'CODE_REVIEW': { id: 'CODE_REVIEW', title: 'Code Review' },
    'DONE': { id: 'DONE', title: 'Done' },
};

export default function SprintBoard() {
    const [tickets, setTickets] = useState<Ticket[]>([]);

    const fetchTickets = useCallback(async () => {
        try {
            const res = await api.get('/tickets');
            setTickets(res.data);
        } catch (error) {
            console.error("Failed to fetch tickets", error);
        }
    }, []);

    useEffect(() => {
        // eslint-disable-next-line
        fetchTickets();
    }, [fetchTickets]);

    const getTicketsByStatus = (status: string) => {
        return tickets.filter(t => t.status === status);
    };

    const onDragEnd = async (result: DropResult) => {
        const { destination, source, draggableId } = result;

        if (!destination) return;
        if (destination.droppableId === source.droppableId && destination.index === source.index) return;

        const ticketId = parseInt(draggableId);
        const newStatus = destination.droppableId;

        // Optimistic update
        const updatedTickets = tickets.map(t =>
            t.id === ticketId ? { ...t, status: newStatus } : t
        );
        setTickets(updatedTickets);

        try {
            await api.patch(`/tickets/${ticketId}`, { status: newStatus });
        } catch (error) {
            console.error("Failed to update ticket", error);
            fetchTickets(); // Revert on error
        }
    };

    return (
        <div className="h-full flex flex-col relative">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-white">Sprint Board</h1>
                <div className="text-sm text-gray-400 italic">
                    Tickets assigned by Manager via Jira Sync
                </div>
            </div>

            <DragDropContext onDragEnd={onDragEnd}>
                <div className="flex-1 flex flex-col md:flex-row gap-4 pb-4 overflow-hidden">
                    {Object.values(columns).map((column) => (
                        <div key={column.id} className="w-full md:flex-1 min-w-0 bg-gray-900/50 rounded-xl border border-gray-800 flex flex-col">
                            <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900 rounded-t-xl">
                                <h3 className="font-semibold text-gray-300">{column.title}</h3>
                                <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                                    {getTicketsByStatus(column.id).length}
                                </span>
                            </div>

                            <Droppable droppableId={column.id}>
                                {(provided, snapshot) => (
                                    <div
                                        ref={provided.innerRef}
                                        {...provided.droppableProps}
                                        className={`flex-1 p-3 space-y-3 transition-colors ${snapshot.isDraggingOver ? 'bg-gray-800/30' : ''}`}
                                    >
                                        {getTicketsByStatus(column.id).map((ticket, index) => (
                                            <Draggable key={ticket.id} draggableId={ticket.id.toString()} index={index}>
                                                {(provided, snapshot) => (
                                                    <div
                                                        ref={provided.innerRef}
                                                        {...provided.draggableProps}
                                                        {...provided.dragHandleProps}
                                                        className={`bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-sm hover:border-gray-600 group cursor-move ${snapshot.isDragging ? 'opacity-50 ring-2 ring-blue-500' : ''}`}
                                                        style={provided.draggableProps.style}
                                                    >
                                                        <div className="flex justify-between items-start mb-2">
                                                            <span className={`text-xs px-2 py-0.5 rounded ${ticket.priority === 'HIGH' ? 'bg-red-500/20 text-red-400' : ticket.priority === 'CRITICAL' ? 'bg-red-600/20 text-red-500 font-bold' : 'bg-green-500/20 text-green-400'}`}>
                                                                {ticket.priority}
                                                            </span>
                                                        </div>
                                                        <h4 className="font-medium text-white mb-1">{ticket.title}</h4>

                                                        {ticket.due_date && (
                                                            <div className="flex items-center text-xs text-orange-400 mt-2 mb-2">
                                                                <Calendar className="w-3 h-3 mr-1" />
                                                                {new Date(ticket.due_date).toLocaleDateString()}
                                                            </div>
                                                        )}

                                                        <div className="flex items-center justify-between mt-3">
                                                            <div className="flex -space-x-2">
                                                                <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-[10px] ring-2 ring-gray-800">
                                                                    ME
                                                                </div>
                                                            </div>
                                                            <span className="text-xs text-gray-500">#{ticket.id}</span>
                                                        </div>
                                                    </div>
                                                )}
                                            </Draggable>
                                        ))}
                                        {provided.placeholder}
                                    </div>
                                )}
                            </Droppable>
                        </div>
                    ))}
                </div>
            </DragDropContext>
        </div>
    );
}
