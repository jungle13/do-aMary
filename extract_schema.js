const { Client } = require('pg');
const fs = require('fs');

async function extractSchema() {
    const client = new Client({
        connectionString: 'postgresql://postgres:FsKQonYRTPZzYRbg@db.ffclvijngnaliiarmjpb.supabase.co:5432/postgres'
    });

    try {
        await client.connect();
        
        let output = '-- ESQUEMA ACTUALIZADO DE SUPABASE (Generado via pg)\n';
        output += '-- Fecha: ' + new Date().toISOString() + '\n\n';
        
        // Get Tables
        const resTables = await client.query(`
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type IN ('BASE TABLE', 'VIEW')
        `);
        
        for (const row of resTables.rows) {
            const tableName = row.table_name;
            output += `CREATE TABLE public.${tableName} (\n`;
            
            const resCols = await client.query(`
                SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            `, [tableName]);
            
            const cols = resCols.rows.map(col => {
                let typeStr = col.data_type;
                if (col.character_maximum_length) {
                    typeStr += `(${col.character_maximum_length})`;
                }
                let nullableStr = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
                let defStr = col.column_default ? ` DEFAULT ${col.column_default}` : '';
                return `    ${col.column_name} ${typeStr} ${nullableStr}${defStr}`;
            });
            
            output += cols.join(',\n') + '\n);\n\n';
        }
        
        // Get RPCs (functions)
        const resFuncs = await client.query(`
            SELECT p.proname AS func_name,
                   pg_get_function_arguments(p.oid) AS func_args,
                   pg_get_function_result(p.oid) AS func_result
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public'
            AND p.prokind = 'f'
        `);
        
        output += '-- ==========================================\n';
        output += '-- FUNCIONES RPC\n';
        output += '-- ==========================================\n\n';
        
        for (const row of resFuncs.rows) {
            output += `CREATE FUNCTION public.${row.func_name}(${row.func_args})\n`;
            output += `RETURNS ${row.func_result} AS $$\n`;
            output += `  -- Logic\n`;
            output += `$$ LANGUAGE plpgsql;\n\n`;
        }
        
        fs.writeFileSync('esquema_actualizado.sql', output);
        console.log('Schema extracted successfully');
        
    } catch (err) {
        console.error('Error extracting schema:', err);
    } finally {
        await client.end();
    }
}

extractSchema();
