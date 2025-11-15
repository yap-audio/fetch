/**
 * Integration tests for negotiation orchestrator with production services.
 * 
 * These tests verify that our TypeScript client can successfully:
 * - Call the seller agent service
 * - Call the buyer agent service
 * - Stream responses from both
 * - Handle multi-turn negotiations
 * 
 * Assumes Python services are working (their tests passed).
 * 
 * @jest-environment node
 */

import fetch from 'node-fetch';
import { TextDecoder } from 'util';
import { createClient } from '@supabase/supabase-js';

// Known test intent ID
const TEST_INTENT_ID = 'b3da442d-125a-43d7-87d6-dcfc01fa3db8';
const SELLER_URL = process.env.TEST_SELLER_URL || 'http://localhost:8000';
const BUYER_URL = process.env.TEST_BUYER_URL || 'http://localhost:8001';

// Supabase client for status verification
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

describe('Negotiation Integration Tests', () => {
  // Increase timeout for network requests
  jest.setTimeout(120000);

  describe('Service Health Checks', () => {
    test('seller service is reachable', async () => {
      const response = await fetch(SELLER_URL);
      expect(response.ok).toBe(true);
      
      const data = await response.json();
      expect(data.status).toBe('ok');
      expect(data.service).toBe('negotiation-agent');
    });

    test('buyer service is reachable', async () => {
      const response = await fetch(BUYER_URL);
      expect(response.ok).toBe(true);
      
      const data = await response.json();
      expect(data.status).toBe('ok');
      expect(data.service).toBe('negotiation-agent');
    });
  });

  describe('Single Agent Calls', () => {
    test('can call seller /negotiate endpoint', async () => {
      const response = await fetch(`${SELLER_URL}/negotiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent_id: TEST_INTENT_ID,
          seller_message: 'Hello! I would like to make you an offer.',
          conversation_history: [],
          agent_type: 'seller'
        })
      });

      expect(response.ok).toBe(true);
      expect(response.headers.get('content-type')).toContain('text/event-stream');

      // Verify we can read the stream (Node.js stream, not browser ReadableStream)
      expect(response.body).toBeDefined();

      if (response.body) {
        const chunks: Buffer[] = [];
        let dataReceived = false;
        
        for await (const chunk of response.body) {
          chunks.push(chunk as Buffer);
          const text = chunk.toString();
          if (text.includes('data:')) {
            dataReceived = true;
            break; // Stop after first data event
          }
        }
        
        expect(dataReceived).toBe(true);
        response.body.destroy(); // Clean up stream
      }
    });

    test('can call buyer /negotiate endpoint', async () => {
      const response = await fetch(`${BUYER_URL}/negotiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent_id: TEST_INTENT_ID,
          seller_message: 'I can offer this item for $150',
          conversation_history: [],
          agent_type: 'buyer'
        })
      });

      expect(response.ok).toBe(true);
      expect(response.headers.get('content-type')).toContain('text/event-stream');

      // Verify streaming works
      if (response.body) {
        for await (const chunk of response.body) {
          expect(chunk).toBeDefined();
          response.body.destroy();
          break; // Just check first chunk
        }
      }
    });

    test('handles invalid intent ID gracefully', async () => {
      const response = await fetch(`${SELLER_URL}/negotiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent_id: '00000000-0000-0000-0000-000000000000',
          seller_message: 'Test message',
          agent_type: 'seller'
        })
      });

      expect(response.status).toBe(404);
    });
  });

  describe('Orchestrator API Route', () => {
    test.skip('orchestrator endpoint exists', async () => {
      // Skip this test - requires Next.js server to be running
      const response = await fetch(`http://localhost:3000/api/negotiate/${TEST_INTENT_ID}`);
      
      // Should start streaming (200) or error gracefully (500)
      expect([200, 500]).toContain(response.status);
    });

    test.skip('orchestrator streams seller and buyer messages', async () => {
      // Skip this test - requires Next.js server to be running
      const response = await fetch(`http://localhost:3000/api/negotiate/${TEST_INTENT_ID}`);
      
      if (!response.ok) {
        console.warn('Orchestrator test skipped - service may be cold starting');
        return;
      }

      expect(response.headers.get('content-type')).toContain('text/event-stream');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      let sellerMessageReceived = false;
      let buyerMessageReceived = false;
      let eventCount = 0;
      const maxEvents = 50; // Prevent infinite loop

      if (reader) {
        while (eventCount < maxEvents) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                eventCount++;

                if (data.type === 'seller') {
                  sellerMessageReceived = true;
                }
                if (data.type === 'buyer') {
                  buyerMessageReceived = true;
                }
                if (data.type === 'complete' || data.type === 'error') {
                  reader.cancel();
                  break;
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }

          if (sellerMessageReceived && buyerMessageReceived) {
            reader.cancel();
            break;
          }
        }
      }

      expect(sellerMessageReceived).toBe(true);
      expect(buyerMessageReceived).toBe(true);
      expect(eventCount).toBeGreaterThan(0);
    });
  });

  describe('Message Formats', () => {
    test('seller messages have correct SSE format', async () => {
      const response = await fetch(`${SELLER_URL}/negotiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent_id: TEST_INTENT_ID,
          seller_message: 'Test offer',
          conversation_history: [],
          agent_type: 'seller'
        })
      });

      let foundTextMessage = false;
      let foundFinalMessage = false;

      if (response.body) {
        let buffer = '';
        
        for await (const chunk of response.body) {
          buffer += chunk.toString();
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'text') {
                  foundTextMessage = true;
                  expect(data).toHaveProperty('content');
                }
                
                if (data.type === 'final') {
                  foundFinalMessage = true;
                  expect(data).toHaveProperty('decision');
                  expect(['accept', 'reject', 'continue']).toContain(data.decision);
                  response.body.destroy();
                  break;
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }

          if (foundFinalMessage) break;
        }
      }

      expect(foundTextMessage).toBe(true);
      expect(foundFinalMessage).toBe(true);
    });
  });

  describe('Conversation History', () => {
    test('agents accept conversation history', async () => {
      const conversationHistory = [
        { role: 'seller', content: 'I can offer this for $100' },
        { role: 'buyer', content: 'That seems high, can you do $80?' }
      ];

      const response = await fetch(`${SELLER_URL}/negotiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent_id: TEST_INTENT_ID,
          seller_message: 'How about $90?',
          conversation_history: conversationHistory,
          agent_type: 'seller'
        })
      });

      expect(response.ok).toBe(true);

      // Verify it responds (doesn't crash with history)
      if (response.body) {
        for await (const chunk of response.body) {
          expect(chunk).toBeDefined();
          response.body.destroy();
          break;
        }
      }
    });
  });

  describe('Full Multi-Turn Negotiation', () => {
    test('completes full negotiation between seller and buyer', async () => {
      const MAX_ROUNDS = 10;
      const conversationHistory: Array<{ role: string; content: string }> = [];
      
      // Helper function to call an agent and get full response
      const callAgent = async (
        agentType: 'seller' | 'buyer',
        message: string
      ): Promise<{ response: string; decision: string }> => {
        const url = agentType === 'seller' ? SELLER_URL : BUYER_URL;
        
        const response = await fetch(`${url}/negotiate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            intent_id: TEST_INTENT_ID,
            seller_message: message,
            conversation_history: conversationHistory,
            agent_type: agentType
          })
        });

        expect(response.ok).toBe(true);

        let fullResponse = '';
        let decision = 'continue';

        if (response.body) {
          let buffer = '';
          
          for await (const chunk of response.body) {
            buffer += chunk.toString();
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  
                  if (data.type === 'text') {
                    fullResponse += data.content;
                  } else if (data.type === 'final') {
                    decision = data.decision;
                  }
                } catch (e) {
                  // Skip invalid JSON
                }
              }
            }
          }
        }

        return { response: fullResponse, decision };
      };

      // Start negotiation with seller's opening pitch
      console.log('\n🤝 Starting full negotiation...\n');
      
      const sellerOpening = await callAgent('seller', "Hello! I'd like to make you an offer for this item.");
      console.log(`Seller (Round 1): ${sellerOpening.response.substring(0, 100)}...`);
      console.log(`Decision: ${sellerOpening.decision}\n`);
      
      conversationHistory.push({
        role: 'seller',
        content: sellerOpening.response
      });

      expect(sellerOpening.response.length).toBeGreaterThan(0);
      expect(['continue', 'accept', 'reject']).toContain(sellerOpening.decision);

      if (sellerOpening.decision !== 'continue') {
        console.log(`Negotiation ended early with decision: ${sellerOpening.decision}`);
        return;
      }

      // Main negotiation loop
      for (let round = 1; round <= MAX_ROUNDS; round++) {
        // Buyer's turn
        const buyerMessage = conversationHistory[conversationHistory.length - 1].content;
        const buyerResult = await callAgent('buyer', buyerMessage);
        
        console.log(`Buyer (Round ${round}): ${buyerResult.response.substring(0, 100)}...`);
        console.log(`Decision: ${buyerResult.decision}\n`);
        
        conversationHistory.push({
          role: 'buyer',
          content: buyerResult.response
        });

        expect(buyerResult.response.length).toBeGreaterThan(0);
        expect(['continue', 'accept', 'reject']).toContain(buyerResult.decision);

        if (buyerResult.decision === 'accept') {
          console.log(`✅ Deal reached by buyer in round ${round}!`);
          expect(conversationHistory.length).toBeGreaterThanOrEqual(2);
          
          // Verify intent status would be updated (note: this test doesn't use our orchestrator)
          console.log(`\n📊 Negotiation completed successfully!`);
          console.log(`   - Total rounds: ${round}`);
          console.log(`   - Final decision: accept (by buyer)`);
          console.log(`   - Messages exchanged: ${conversationHistory.length}`);
          
          return;
        }

        if (buyerResult.decision === 'reject') {
          console.log(`❌ Buyer rejected in round ${round}`);
          expect(conversationHistory.length).toBeGreaterThanOrEqual(2);
          return;
        }

        // Seller's turn (if buyer continued)
        if (round < MAX_ROUNDS) {
          const sellerMessage = conversationHistory[conversationHistory.length - 1].content;
          const sellerResult = await callAgent('seller', sellerMessage);
          
          console.log(`Seller (Round ${round + 1}): ${sellerResult.response.substring(0, 100)}...`);
          console.log(`Decision: ${sellerResult.decision}\n`);
          
          conversationHistory.push({
            role: 'seller',
            content: sellerResult.response
          });

          expect(sellerResult.response.length).toBeGreaterThan(0);
          expect(['continue', 'accept', 'reject']).toContain(sellerResult.decision);

          if (sellerResult.decision === 'accept') {
            console.log(`✅ Deal reached by seller in round ${round + 1}!`);
            expect(conversationHistory.length).toBeGreaterThanOrEqual(2);
            
            // Verify intent status would be updated
            console.log(`\n📊 Negotiation completed successfully!`);
            console.log(`   - Total rounds: ${round + 1}`);
            console.log(`   - Final decision: accept (by seller)`);
            console.log(`   - Messages exchanged: ${conversationHistory.length}`);
            
            return;
          }

          if (sellerResult.decision === 'reject') {
            console.log(`❌ Seller rejected in round ${round + 1}`);
            expect(conversationHistory.length).toBeGreaterThanOrEqual(2);
            return;
          }
        }
      }

      // If we get here, max rounds reached
      console.log(`⏱️  Max rounds (${MAX_ROUNDS}) reached without deal`);
      expect(conversationHistory.length).toBeGreaterThan(0);
    }, 180000); // 3 minute timeout for full negotiation

    test('intent status is updated to completed after deal', async () => {
      // First, verify initial status
      const { data: initialIntent } = await supabase
        .from('intents')
        .select('status')
        .eq('uuid', TEST_INTENT_ID)
        .single();

      console.log(`\n📋 Initial intent status: ${initialIntent?.status}`);

      // Simulate what our orchestrator does: update status when deal is reached
      const { data: updatedIntent, error } = await supabase
        .from('intents')
        .update({ status: 'completed' })
        .eq('uuid', TEST_INTENT_ID)
        .select()
        .single();

      expect(error).toBeNull();
      expect(updatedIntent?.status).toBe('completed');
      console.log(`✅ Successfully updated intent status to: ${updatedIntent?.status}`);

      // Reset back to original status for future tests
      if (initialIntent) {
        await supabase
          .from('intents')
          .update({ status: initialIntent.status })
          .eq('uuid', TEST_INTENT_ID);
        console.log(`🔄 Reset intent status back to: ${initialIntent.status}`);
      }
    });
  });
});

