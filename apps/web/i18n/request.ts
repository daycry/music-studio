import {getRequestConfig} from 'next-intl/server';
import messages from '../messages/es.json';
export default getRequestConfig(async()=>({locale:'es',messages}));
