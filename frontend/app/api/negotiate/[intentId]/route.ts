import { NextRequest } from 'next/server';
import { supabase } from '@/lib/supabase';
import { Database } from '@/lib/database.types';

const SELLER_URL = process.env.NEXT_PUBLIC_SELLER_AGENT_URL || '';
const BUYER_URL = process.env.NEXT_PUBLIC_BUYER_AGENT_URL || '';
const MAX_ROUNDS = 10;

type IntentUpdate = Database['public']['Tables']['intents']['Update'];

interface ConversationEntry {
  role: 'seller' | 'buyer';
  content: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ intentId: string }> }
) {
  const { intentId } = await params;

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Helper to send SSE message
        const sendEvent = (data: any) => {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(data)}\n\n`)
          );
        };

        const conversationHistory: ConversationEntry[] = [];
        let currentRound = 0;

        // Helper to call an agent and stream response
        const callAgent = async (
          agentType: 'seller' | 'buyer',
          message: string
        ): Promise<{ response: string; decision: string }> => {
          const url = agentType === 'seller' ? SELLER_URL : BUYER_URL;
          
          sendEvent({
            type: agentType,
            phase: 'thinking',
            content: '',
            round: currentRound + 1
          });

          const requestBody = {
            intent_id: intentId,
            seller_message: message,
            conversation_history: conversationHistory,
            agent_type: agentType
          };

          console.log(`Calling ${agentType} agent:`, {
            url: `${url}/negotiate`,
            intentId,
            messageLength: message.length,
            historyLength: conversationHistory.length
          });

          const response = await fetch(`${url}/negotiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error(`${agentType} agent error:`, {
              status: response.status,
              statusText: response.statusText,
              body: errorText
            });
            throw new Error(`${agentType} agent returned ${response.status}: ${errorText}`);
          }

          let fullResponse = '';
          let decision = 'continue';
          let paymentResult = null;
          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (reader) {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'text') {
                      fullResponse += data.content;
                      // Stream the text chunk to frontend
                      sendEvent({
                        type: agentType,
                        phase: 'response',
                        content: data.content,
                        round: currentRound + 1
                      });
                    } else if (data.type === 'final') {
                      decision = data.decision || 'continue';
                      paymentResult = data.payment_result || null;
                    }
                  } catch (e) {
                    // Skip invalid JSON
                  }
                }
              }
            }
          }

          // Send decision with payment result
          sendEvent({
            type: agentType,
            phase: 'decision',
            decision,
            payment_result: paymentResult,
            round: currentRound + 1
          });

          return { response: fullResponse, decision };
        };

        // Start negotiation with seller's opening pitch
        sendEvent({
          type: 'start',
          content: 'Starting negotiation...',
          maxRounds: MAX_ROUNDS
        });

        // Seller makes opening offer
        const initialOffer = "Hello! I'd like to make you an offer for this item.";
        const sellerResult = await callAgent('seller', initialOffer);
        
        conversationHistory.push({
          role: 'seller',
          content: sellerResult.response
        });

        if (sellerResult.decision === 'reject') {
          sendEvent({
            type: 'complete',
            outcome: 'rejected',
            rounds: 1,
            finalDecisionBy: 'seller'
          });
          controller.close();
          return;
        }

        // Main negotiation loop
        for (currentRound = 0; currentRound < MAX_ROUNDS; currentRound++) {
          // Buyer's turn
          const buyerMessage = conversationHistory[conversationHistory.length - 1].content;
          const buyerResult = await callAgent('buyer', buyerMessage);
          
          conversationHistory.push({
            role: 'buyer',
            content: buyerResult.response
          });

          if (buyerResult.decision === 'accept') {
            // Update intent status to completed
            await (supabase.from('intents') as any)
              .update({ status: 'completed' })
              .eq('uuid', intentId);

            sendEvent({
              type: 'complete',
              outcome: 'accepted',
              rounds: currentRound + 1,
              finalDecisionBy: 'buyer'
            });
            controller.close();
            return;
          }

          if (buyerResult.decision === 'reject') {
            sendEvent({
              type: 'complete',
              outcome: 'rejected',
              rounds: currentRound + 1,
              finalDecisionBy: 'buyer'
            });
            controller.close();
            return;
          }

          // If buyer continues, seller responds
          if (currentRound < MAX_ROUNDS - 1) {
            const sellerMessage = conversationHistory[conversationHistory.length - 1].content;
            const sellerResult = await callAgent('seller', sellerMessage);
            
            conversationHistory.push({
              role: 'seller',
              content: sellerResult.response
            });

            if (sellerResult.decision === 'accept') {
              // Update intent status to completed
              await (supabase.from('intents') as any)
                .update({ status: 'completed' })
                .eq('uuid', intentId);

              sendEvent({
                type: 'complete',
                outcome: 'accepted',
                rounds: currentRound + 1,
                finalDecisionBy: 'seller'
              });
              controller.close();
              return;
            }

            if (sellerResult.decision === 'reject') {
              sendEvent({
                type: 'complete',
                outcome: 'rejected',
                rounds: currentRound + 1,
                finalDecisionBy: 'seller'
              });
              controller.close();
              return;
            }
          }
        }

        // Max rounds reached
        sendEvent({
          type: 'complete',
          outcome: 'max_rounds_reached',
          rounds: MAX_ROUNDS
        });
        controller.close();

      } catch (error) {
        console.error('Negotiation error:', error);
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({
            type: 'error',
            content: error instanceof Error ? error.message : 'Unknown error'
          })}\n\n`)
        );
        controller.close();
      }
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    }
  });
}

